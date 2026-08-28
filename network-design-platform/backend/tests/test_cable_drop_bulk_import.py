import pytest


@pytest.fixture()
def site_id(client):
    return client.post("/sites", json={"building_code": "27Q273", "name": "PS 273"}).json()["id"]


def test_create_with_vlan_fields(client, site_id):
    resp = client.post(
        f"/sites/{site_id}/cable-drops",
        json={"drop_number": "D001", "vlan": "VLAN 10", "voice_vlan": "VLAN 110"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["vlan"] == "VLAN 10"
    assert body["voice_vlan"] == "VLAN 110"


def test_update_vlan_fields(client, site_id):
    drop = client.post(f"/sites/{site_id}/cable-drops", json={"drop_number": "D001"}).json()
    resp = client.patch(f"/cable-drops/{drop['id']}", json={"vlan": "VLAN 20"})
    assert resp.status_code == 200
    assert resp.json()["vlan"] == "VLAN 20"


def test_bulk_import_creates_new_drops(client, site_id):
    resp = client.post(
        f"/sites/{site_id}/cable-drops/bulk",
        json={
            "rows": [
                {"drop_number": "D001", "vlan": "VLAN 10", "status": "as_built"},
                {"drop_number": "D002", "vlan": "VLAN 20"},
            ]
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["created"] == 2
    assert body["updated"] == 0
    assert body["errors"] == 0
    assert all(r["action"] == "created" for r in body["results"])

    listed = client.get(f"/sites/{site_id}/cable-drops").json()
    assert len(listed) == 2
    d001 = next(d for d in listed if d["drop_number"] == "D001")
    assert d001["vlan"] == "VLAN 10"
    assert d001["status"] == "as_built"


def test_bulk_import_upserts_existing_drops(client, site_id):
    client.post(f"/sites/{site_id}/cable-drops", json={"drop_number": "D001", "vlan": "VLAN 10"})

    resp = client.post(
        f"/sites/{site_id}/cable-drops/bulk",
        json={"rows": [{"drop_number": "D001", "vlan": "VLAN 99", "status": "as_built"}]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["created"] == 0
    assert body["updated"] == 1
    assert body["results"][0]["action"] == "updated"

    listed = client.get(f"/sites/{site_id}/cable-drops").json()
    assert len(listed) == 1
    assert listed[0]["vlan"] == "VLAN 99"
    assert listed[0]["status"] == "as_built"


def test_bulk_import_resolves_room_by_name(client, site_id):
    room = client.post(f"/sites/{site_id}/rooms", json={"name": "Room 101"}).json()

    resp = client.post(
        f"/sites/{site_id}/cable-drops/bulk",
        json={"rows": [{"drop_number": "D001", "room_name": "Room 101"}]},
    )
    assert resp.status_code == 200
    assert resp.json()["created"] == 1

    listed = client.get(f"/sites/{site_id}/cable-drops").json()
    assert listed[0]["room_id"] == room["id"]


def test_bulk_import_unknown_room_reported_as_error_not_crash(client, site_id):
    resp = client.post(
        f"/sites/{site_id}/cable-drops/bulk",
        json={
            "rows": [
                {"drop_number": "D001", "room_name": "Nonexistent Room"},
                {"drop_number": "D002"},
            ]
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["created"] == 1
    assert body["errors"] == 1
    error_row = next(r for r in body["results"] if r["drop_number"] == "D001")
    assert error_row["action"] == "error"
    assert "Nonexistent Room" in error_row["detail"]

    # D002 (no room) still got created despite D001 failing -- one bad row
    # doesn't sink the whole import.
    listed = client.get(f"/sites/{site_id}/cable-drops").json()
    assert len(listed) == 1
    assert listed[0]["drop_number"] == "D002"


def test_bulk_import_unknown_site_404(client):
    resp = client.post("/sites/999/cable-drops/bulk", json={"rows": [{"drop_number": "D001"}]})
    assert resp.status_code == 404
