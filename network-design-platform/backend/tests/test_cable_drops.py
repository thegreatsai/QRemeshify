import pytest


@pytest.fixture()
def site_id(client):
    return client.post("/sites", json={"building_code": "27Q273", "name": "PS 273"}).json()["id"]


@pytest.fixture()
def rack_id(site_id, client):
    return client.post(f"/sites/{site_id}/racks", json={"rack_number": "Rack 1", "total_u": 12}).json()["id"]


def _make_panel(client, rack_id, name, start_u, port_count):
    item = client.post(
        f"/racks/{rack_id}/items",
        json={"name": name, "equipment_type": "patch_panel", "start_u": start_u, "size_u": 1},
    ).json()
    panel = client.post(f"/racks/{rack_id}/items/{item['id']}/patch-panel", json={"port_count": port_count}).json()
    return item, panel


def test_create_and_list_cable_drops(client, site_id):
    resp = client.post(f"/sites/{site_id}/cable-drops", json={"drop_number": "D001"})
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["drop_number"] == "D001"
    assert body["status"] == "draft"
    assert body["port_location"] is None

    resp = client.get(f"/sites/{site_id}/cable-drops")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_duplicate_drop_number_rejected(client, site_id):
    client.post(f"/sites/{site_id}/cable-drops", json={"drop_number": "D001"})
    resp = client.post(f"/sites/{site_id}/cable-drops", json={"drop_number": "D001"})
    assert resp.status_code == 409


def test_assign_drop_to_port_shows_up_in_drop_list(client, site_id, rack_id):
    _, panel = _make_panel(client, rack_id, "Patch Panel A", 1, 4)
    port_id = panel["ports"][0]["id"]
    drop = client.post(f"/sites/{site_id}/cable-drops", json={"drop_number": "D001"}).json()

    resp = client.post(f"/cable-drops/{drop['id']}/assign", json={"port_id": port_id})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["port_location"]["port_id"] == port_id
    assert body["port_location"]["rack_item_name"] == "Patch Panel A"

    # The Drop List view (GET .../cable-drops) reads the exact same row --
    # no separate sync step needed for the assignment to show up there.
    listed = client.get(f"/sites/{site_id}/cable-drops").json()
    assert listed[0]["port_location"]["port_id"] == port_id

    # And the Patch Panel view (GET the panel) shows the drop from the same row.
    panel_after = client.get(f"/patch-panels/{panel['id']}").json()
    assigned_port = next(p for p in panel_after["ports"] if p["id"] == port_id)
    assert assigned_port["status"] == "patched"
    assert assigned_port["cable_drop"]["drop_number"] == "D001"


def test_assigning_to_occupied_port_rejected(client, site_id, rack_id):
    _, panel = _make_panel(client, rack_id, "Panel A", 1, 4)
    port_id = panel["ports"][0]["id"]
    drop_a = client.post(f"/sites/{site_id}/cable-drops", json={"drop_number": "D001"}).json()
    drop_b = client.post(f"/sites/{site_id}/cable-drops", json={"drop_number": "D002"}).json()

    client.post(f"/cable-drops/{drop_a['id']}/assign", json={"port_id": port_id})
    resp = client.post(f"/cable-drops/{drop_b['id']}/assign", json={"port_id": port_id})
    assert resp.status_code == 409
    assert "D001" in resp.json()["detail"]


def test_move_drop_between_patch_panels_updates_drop_list(client, site_id, rack_id):
    """The core ask: moving a drop from one patch panel's port to another's
    must be reflected in the Drop List instantly -- because it's the same
    underlying row, not two copies to reconcile."""
    _, panel_a = _make_panel(client, rack_id, "Panel A", 1, 4)
    _, panel_b = _make_panel(client, rack_id, "Panel B", 6, 4)
    port_a1 = panel_a["ports"][0]["id"]
    port_b1 = panel_b["ports"][0]["id"]

    drop = client.post(f"/sites/{site_id}/cable-drops", json={"drop_number": "D001"}).json()
    client.post(f"/cable-drops/{drop['id']}/assign", json={"port_id": port_a1})

    # Confirm it's on panel A first.
    listed = client.get(f"/sites/{site_id}/cable-drops").json()
    assert listed[0]["port_location"]["patch_panel_id"] == panel_a["id"]
    panel_a_after = client.get(f"/patch-panels/{panel_a['id']}").json()
    assert panel_a_after["ports"][0]["cable_drop"]["drop_number"] == "D001"

    # Move it to panel B.
    resp = client.post(f"/cable-drops/{drop['id']}/assign", json={"port_id": port_b1})
    assert resp.status_code == 200
    assert resp.json()["port_location"]["patch_panel_id"] == panel_b["id"]

    # Drop List reflects the new panel immediately.
    listed = client.get(f"/sites/{site_id}/cable-drops").json()
    assert listed[0]["port_location"]["patch_panel_id"] == panel_b["id"]
    assert listed[0]["port_location"]["port_id"] == port_b1

    # Panel A's old port is freed...
    panel_a_after = client.get(f"/patch-panels/{panel_a['id']}").json()
    assert panel_a_after["ports"][0]["status"] == "free"
    assert panel_a_after["ports"][0]["cable_drop"] is None

    # ...and Panel B's port now shows the drop.
    panel_b_after = client.get(f"/patch-panels/{panel_b['id']}").json()
    assert panel_b_after["ports"][0]["status"] == "patched"
    assert panel_b_after["ports"][0]["cable_drop"]["drop_number"] == "D001"


def test_reassigning_to_same_port_is_a_noop(client, site_id, rack_id):
    _, panel = _make_panel(client, rack_id, "Panel A", 1, 4)
    port_id = panel["ports"][0]["id"]
    drop = client.post(f"/sites/{site_id}/cable-drops", json={"drop_number": "D001"}).json()

    client.post(f"/cable-drops/{drop['id']}/assign", json={"port_id": port_id})
    resp = client.post(f"/cable-drops/{drop['id']}/assign", json={"port_id": port_id})
    assert resp.status_code == 200
    assert resp.json()["port_location"]["port_id"] == port_id


def test_unassign_frees_the_port(client, site_id, rack_id):
    _, panel = _make_panel(client, rack_id, "Panel A", 1, 4)
    port_id = panel["ports"][0]["id"]
    drop = client.post(f"/sites/{site_id}/cable-drops", json={"drop_number": "D001"}).json()
    client.post(f"/cable-drops/{drop['id']}/assign", json={"port_id": port_id})

    resp = client.post(f"/cable-drops/{drop['id']}/unassign")
    assert resp.status_code == 200
    assert resp.json()["port_location"] is None

    panel_after = client.get(f"/patch-panels/{panel['id']}").json()
    assert panel_after["ports"][0]["status"] == "free"

    # port is free again -- a different drop can now take it
    other = client.post(f"/sites/{site_id}/cable-drops", json={"drop_number": "D002"}).json()
    resp = client.post(f"/cable-drops/{other['id']}/assign", json={"port_id": port_id})
    assert resp.status_code == 200


def test_deleting_assigned_drop_frees_its_port(client, site_id, rack_id):
    _, panel = _make_panel(client, rack_id, "Panel A", 1, 4)
    port_id = panel["ports"][0]["id"]
    drop = client.post(f"/sites/{site_id}/cable-drops", json={"drop_number": "D001"}).json()
    client.post(f"/cable-drops/{drop['id']}/assign", json={"port_id": port_id})

    assert client.delete(f"/cable-drops/{drop['id']}").status_code == 204

    panel_after = client.get(f"/patch-panels/{panel['id']}").json()
    assert panel_after["ports"][0]["status"] == "free"
    assert panel_after["ports"][0]["cable_drop"] is None


def test_list_site_ports_free_only(client, site_id, rack_id):
    _, panel = _make_panel(client, rack_id, "Panel A", 1, 2)
    port_ids = [p["id"] for p in panel["ports"]]
    drop = client.post(f"/sites/{site_id}/cable-drops", json={"drop_number": "D001"}).json()
    client.post(f"/cable-drops/{drop['id']}/assign", json={"port_id": port_ids[0]})

    resp = client.get(f"/sites/{site_id}/ports")
    assert resp.status_code == 200
    all_ports = resp.json()
    assert len(all_ports) == 2
    occupied = next(p for p in all_ports if p["port_id"] == port_ids[0])
    assert occupied["cable_drop_id"] == drop["id"]
    free = next(p for p in all_ports if p["port_id"] == port_ids[1])
    assert free["cable_drop_id"] is None

    resp = client.get(f"/sites/{site_id}/ports", params={"free_only": True})
    assert resp.status_code == 200
    free_ids = [p["port_id"] for p in resp.json()]
    assert free_ids == [port_ids[1]]
