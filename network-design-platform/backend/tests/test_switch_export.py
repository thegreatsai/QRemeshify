import pytest


@pytest.fixture()
def site_id(client):
    return client.post("/sites", json={"building_code": "27Q273", "name": "PS 273"}).json()["id"]


@pytest.fixture()
def rack_id(site_id, client):
    return client.post(f"/sites/{site_id}/racks", json={"rack_number": "Rack 1", "total_u": 12}).json()["id"]


def _make_switch(client, rack_id, model, port_count=4):
    item = client.post(
        f"/racks/{rack_id}/items",
        json={"name": "Core Switch", "equipment_type": "switch", "start_u": 1, "size_u": 1},
    ).json()
    return client.post(
        f"/racks/{rack_id}/items/{item['id']}/switch", json={"model": model, "port_count": port_count}
    ).json()


def test_export_ios_switch_returns_cli_text(client, site_id, rack_id):
    switch = _make_switch(client, rack_id, "Cisco 9300-48")
    vlan = client.post(f"/sites/{site_id}/vlans", json={"vlan_number": 10, "name": "Instructional"}).json()
    client.patch(
        f"/switches/{switch['id']}/ports/{switch['ports'][0]['id']}",
        json={"vlan_id": vlan["id"], "description": "Room 101"},
    )

    resp = client.get(f"/switches/{switch['id']}/export")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/plain")
    assert "interface GigabitEthernet1/0/1" in resp.text
    assert " switchport access vlan 10" in resp.text
    assert " description Room 101" in resp.text


def test_export_meraki_switch_returns_json(client, rack_id):
    switch = _make_switch(client, rack_id, "MS390-24")
    resp = client.get(f"/switches/{switch['id']}/export")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/json")
    body = resp.json()
    assert len(body) == 4
    assert body[0]["portId"] == "1"


def test_export_custom_interface_prefix(client, rack_id):
    switch = _make_switch(client, rack_id, "Cisco 9300-48")
    resp = client.get(f"/switches/{switch['id']}/export", params={"interface_prefix": "TenGigabitEthernet1/1/"})
    assert "interface TenGigabitEthernet1/1/1" in resp.text


def test_export_unknown_switch_404(client):
    resp = client.get("/switches/999/export")
    assert resp.status_code == 404
