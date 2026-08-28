import pytest


@pytest.fixture()
def site_id(client):
    return client.post("/sites", json={"building_code": "27Q273", "name": "PS 273"}).json()["id"]


@pytest.fixture()
def rack_id(site_id, client):
    return client.post(f"/sites/{site_id}/racks", json={"rack_number": "Rack 1", "total_u": 12}).json()["id"]


def _make_switch(client, rack_id, name, start_u, port_count, model="Cisco 9300-48"):
    item = client.post(
        f"/racks/{rack_id}/items",
        json={"name": name, "equipment_type": "switch", "start_u": start_u, "size_u": 1},
    ).json()
    switch = client.post(
        f"/racks/{rack_id}/items/{item['id']}/switch", json={"model": model, "port_count": port_count}
    ).json()
    return item, switch


def test_create_switch_creates_ports(client, site_id, rack_id):
    item, switch = _make_switch(client, rack_id, "Core Switch", 1, 8)
    assert switch["model"] == "Cisco 9300-48"
    assert switch["port_count"] == 8
    assert len(switch["ports"]) == 8
    assert [p["port_number"] for p in switch["ports"]] == list(range(1, 9))
    assert all(p["mode"] == "access" for p in switch["ports"])
    assert all(p["vlan"] is None for p in switch["ports"])


def test_rack_item_read_surfaces_switch_summary(client, rack_id):
    item, switch = _make_switch(client, rack_id, "Core Switch", 1, 8)
    items = client.get(f"/racks/{rack_id}/items").json()
    listed = next(i for i in items if i["id"] == item["id"])
    assert listed["switch"] == {"id": switch["id"], "model": "Cisco 9300-48", "port_count": 8}


def test_duplicate_switch_on_same_item_rejected(client, rack_id):
    item, _ = _make_switch(client, rack_id, "Core Switch", 1, 8)
    resp = client.post(f"/racks/{rack_id}/items/{item['id']}/switch", json={"model": "x", "port_count": 8})
    assert resp.status_code == 409


def test_create_vlan(client, site_id):
    resp = client.post(f"/sites/{site_id}/vlans", json={"vlan_number": 10, "name": "Instructional"})
    assert resp.status_code == 201, resp.text
    assert resp.json()["vlan_number"] == 10


def test_duplicate_vlan_number_rejected(client, site_id):
    client.post(f"/sites/{site_id}/vlans", json={"vlan_number": 10, "name": "Instructional"})
    resp = client.post(f"/sites/{site_id}/vlans", json={"vlan_number": 10, "name": "Other"})
    assert resp.status_code == 409


def test_assign_vlan_to_switch_port(client, site_id, rack_id):
    _, switch = _make_switch(client, rack_id, "Core Switch", 1, 8)
    vlan = client.post(f"/sites/{site_id}/vlans", json={"vlan_number": 10, "name": "Instructional"}).json()
    port_id = switch["ports"][0]["id"]

    resp = client.patch(
        f"/switches/{switch['id']}/ports/{port_id}",
        json={"vlan_id": vlan["id"], "description": "Room 101"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["vlan"]["vlan_number"] == 10
    assert body["description"] == "Room 101"


def test_assign_vlan_from_different_site_rejected(client, rack_id):
    _, switch = _make_switch(client, rack_id, "Core Switch", 1, 8)
    other_site = client.post("/sites", json={"building_code": "30Q149", "name": "PS 149"}).json()["id"]
    vlan = client.post(f"/sites/{other_site}/vlans", json={"vlan_number": 10, "name": "Foreign"}).json()
    port_id = switch["ports"][0]["id"]

    resp = client.patch(f"/switches/{switch['id']}/ports/{port_id}", json={"vlan_id": vlan["id"]})
    assert resp.status_code == 422


def test_delete_vlan_in_use_rejected(client, site_id, rack_id):
    _, switch = _make_switch(client, rack_id, "Core Switch", 1, 8)
    vlan = client.post(f"/sites/{site_id}/vlans", json={"vlan_number": 10, "name": "Instructional"}).json()
    port_id = switch["ports"][0]["id"]
    client.patch(f"/switches/{switch['id']}/ports/{port_id}", json={"vlan_id": vlan["id"]})

    resp = client.delete(f"/vlans/{vlan['id']}")
    assert resp.status_code == 409


def test_delete_unused_vlan_ok(client, site_id):
    vlan = client.post(f"/sites/{site_id}/vlans", json={"vlan_number": 20, "name": "Unused"}).json()
    assert client.delete(f"/vlans/{vlan['id']}").status_code == 204


def test_cross_connect_drop_to_switch_port(client, site_id, rack_id):
    """A drop can be cross-connected to a switch port independently of
    (and at the same time as) being patched into a patch-panel port --
    both hops of the physical chain, both single-source-of-truth fields
    on the same CableDrop row."""
    _, switch = _make_switch(client, rack_id, "Core Switch", 1, 8)
    vlan = client.post(f"/sites/{site_id}/vlans", json={"vlan_number": 10, "name": "Instructional"}).json()
    switch_port_id = switch["ports"][0]["id"]
    client.patch(f"/switches/{switch['id']}/ports/{switch_port_id}", json={"vlan_id": vlan["id"]})

    drop = client.post(f"/sites/{site_id}/cable-drops", json={"drop_number": "D001"}).json()
    resp = client.post(f"/cable-drops/{drop['id']}/assign-switch-port", json={"switch_port_id": switch_port_id})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["switch_port_location"]["switch_port_id"] == switch_port_id
    assert body["switch_port_location"]["vlan_number"] == 10

    # Drop List reads the same row.
    listed = client.get(f"/sites/{site_id}/cable-drops").json()
    assert listed[0]["switch_port_location"]["switch_port_id"] == switch_port_id

    # And the switch's own port view shows the drop.
    switch_after = client.get(f"/switches/{switch['id']}").json()
    port_after = next(p for p in switch_after["ports"] if p["id"] == switch_port_id)
    assert port_after["cable_drop"]["drop_number"] == "D001"


def test_cross_connect_conflict_rejected(client, site_id, rack_id):
    _, switch = _make_switch(client, rack_id, "Core Switch", 1, 8)
    switch_port_id = switch["ports"][0]["id"]
    drop_a = client.post(f"/sites/{site_id}/cable-drops", json={"drop_number": "D001"}).json()
    drop_b = client.post(f"/sites/{site_id}/cable-drops", json={"drop_number": "D002"}).json()

    client.post(f"/cable-drops/{drop_a['id']}/assign-switch-port", json={"switch_port_id": switch_port_id})
    resp = client.post(f"/cable-drops/{drop_b['id']}/assign-switch-port", json={"switch_port_id": switch_port_id})
    assert resp.status_code == 409


def test_unassign_switch_port(client, site_id, rack_id):
    _, switch = _make_switch(client, rack_id, "Core Switch", 1, 8)
    switch_port_id = switch["ports"][0]["id"]
    drop = client.post(f"/sites/{site_id}/cable-drops", json={"drop_number": "D001"}).json()
    client.post(f"/cable-drops/{drop['id']}/assign-switch-port", json={"switch_port_id": switch_port_id})

    resp = client.post(f"/cable-drops/{drop['id']}/unassign-switch-port")
    assert resp.status_code == 200
    assert resp.json()["switch_port_location"] is None

    other = client.post(f"/sites/{site_id}/cable-drops", json={"drop_number": "D002"}).json()
    resp = client.post(f"/cable-drops/{other['id']}/assign-switch-port", json={"switch_port_id": switch_port_id})
    assert resp.status_code == 200


def test_patch_panel_and_switch_port_assignment_are_independent(client, site_id, rack_id):
    """A drop can be patched into a patch-panel port and cross-connected
    to a switch port at the same time -- both are tracked, neither
    clobbers the other."""
    panel_item = client.post(
        f"/racks/{rack_id}/items",
        json={"name": "Patch Panel A", "equipment_type": "patch_panel", "start_u": 6, "size_u": 1},
    ).json()
    panel = client.post(f"/racks/{rack_id}/items/{panel_item['id']}/patch-panel", json={"port_count": 4}).json()
    _, switch = _make_switch(client, rack_id, "Core Switch", 1, 8)

    drop = client.post(f"/sites/{site_id}/cable-drops", json={"drop_number": "D001"}).json()
    client.post(f"/cable-drops/{drop['id']}/assign", json={"port_id": panel["ports"][0]["id"]})
    client.post(
        f"/cable-drops/{drop['id']}/assign-switch-port", json={"switch_port_id": switch["ports"][0]["id"]}
    )

    listed = client.get(f"/sites/{site_id}/cable-drops").json()[0]
    assert listed["port_location"]["patch_panel_id"] == panel["id"]
    assert listed["switch_port_location"]["switch_id"] == switch["id"]


def test_list_site_switch_ports_free_only(client, site_id, rack_id):
    _, switch = _make_switch(client, rack_id, "Core Switch", 1, 4)
    port_ids = [p["id"] for p in switch["ports"]]
    drop = client.post(f"/sites/{site_id}/cable-drops", json={"drop_number": "D001"}).json()
    client.post(f"/cable-drops/{drop['id']}/assign-switch-port", json={"switch_port_id": port_ids[0]})

    resp = client.get(f"/sites/{site_id}/switch-ports", params={"free_only": True})
    assert resp.status_code == 200
    free_ids = [p["switch_port_id"] for p in resp.json()]
    assert port_ids[0] not in free_ids
    assert len(free_ids) == 3
