import pytest


@pytest.fixture()
def rack_id(client):
    site = client.post("/sites", json={"building_code": "27Q273", "name": "PS 273"}).json()
    rack = client.post(f"/sites/{site['id']}/racks", json={"rack_number": "Rack 1", "total_u": 12}).json()
    return rack["id"]


def test_create_and_list_rack_items(client, rack_id):
    resp = client.post(
        f"/racks/{rack_id}/items",
        json={"name": "Core Switch", "equipment_type": "switch", "start_u": 10, "size_u": 1},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["start_u"] == 10

    resp = client.get(f"/racks/{rack_id}/items")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_overlapping_items_rejected(client, rack_id):
    client.post(
        f"/racks/{rack_id}/items",
        json={"name": "Patch Panel A", "equipment_type": "patch_panel", "start_u": 5, "size_u": 2},
    )
    resp = client.post(
        f"/racks/{rack_id}/items",
        json={"name": "Patch Panel B", "equipment_type": "patch_panel", "start_u": 6, "size_u": 2},
    )
    assert resp.status_code == 409
    assert "overlaps" in resp.json()["detail"]


def test_adjacent_items_allowed(client, rack_id):
    client.post(
        f"/racks/{rack_id}/items",
        json={"name": "Panel A", "equipment_type": "patch_panel", "start_u": 5, "size_u": 2},
    )
    resp = client.post(
        f"/racks/{rack_id}/items",
        json={"name": "Panel B", "equipment_type": "patch_panel", "start_u": 7, "size_u": 2},
    )
    assert resp.status_code == 201


def test_item_beyond_rack_capacity_rejected(client, rack_id):
    resp = client.post(
        f"/racks/{rack_id}/items",
        json={"name": "Too Tall", "equipment_type": "shelf", "start_u": 11, "size_u": 5},
    )
    assert resp.status_code == 409
    assert "capacity" in resp.json()["detail"]


def test_move_item_drag_to_place(client, rack_id):
    item = client.post(
        f"/racks/{rack_id}/items",
        json={"name": "Switch", "equipment_type": "switch", "start_u": 1, "size_u": 1},
    ).json()

    resp = client.patch(f"/racks/{rack_id}/items/{item['id']}/move", json={"start_u": 8})
    assert resp.status_code == 200
    assert resp.json()["start_u"] == 8


def test_move_item_into_occupied_slot_rejected(client, rack_id):
    client.post(
        f"/racks/{rack_id}/items",
        json={"name": "Fixed Panel", "equipment_type": "patch_panel", "start_u": 3, "size_u": 2},
    )
    movable = client.post(
        f"/racks/{rack_id}/items",
        json={"name": "Movable Switch", "equipment_type": "switch", "start_u": 10, "size_u": 1},
    ).json()

    resp = client.patch(f"/racks/{rack_id}/items/{movable['id']}/move", json={"start_u": 3})
    assert resp.status_code == 409

    # confirm it did not move
    items = client.get(f"/racks/{rack_id}/items").json()
    moved = next(i for i in items if i["id"] == movable["id"])
    assert moved["start_u"] == 10


def test_move_item_to_its_own_current_slot_allowed(client, rack_id):
    item = client.post(
        f"/racks/{rack_id}/items",
        json={"name": "Panel", "equipment_type": "patch_panel", "start_u": 4, "size_u": 2},
    ).json()

    resp = client.patch(f"/racks/{rack_id}/items/{item['id']}/move", json={"start_u": 4})
    assert resp.status_code == 200


def test_delete_rack_item(client, rack_id):
    item = client.post(
        f"/racks/{rack_id}/items",
        json={"name": "Temp", "equipment_type": "shelf", "start_u": 1, "size_u": 1},
    ).json()
    assert client.delete(f"/racks/{rack_id}/items/{item['id']}").status_code == 204
    assert client.get(f"/racks/{rack_id}/items").json() == []


def test_patch_panel_creates_ports(client, rack_id):
    item = client.post(
        f"/racks/{rack_id}/items",
        json={"name": "Patch Panel", "equipment_type": "patch_panel", "start_u": 1, "size_u": 1},
    ).json()

    resp = client.post(f"/racks/{rack_id}/items/{item['id']}/patch-panel", json={"port_count": 24})
    assert resp.status_code == 201, resp.text
    panel = resp.json()
    assert panel["port_count"] == 24
    assert len(panel["ports"]) == 24
    assert [p["port_number"] for p in panel["ports"]] == list(range(1, 25))
    assert all(p["status"] == "free" for p in panel["ports"])


def test_patch_panel_duplicate_rejected(client, rack_id):
    item = client.post(
        f"/racks/{rack_id}/items",
        json={"name": "Patch Panel", "equipment_type": "patch_panel", "start_u": 1, "size_u": 1},
    ).json()
    client.post(f"/racks/{rack_id}/items/{item['id']}/patch-panel", json={"port_count": 12})
    resp = client.post(f"/racks/{rack_id}/items/{item['id']}/patch-panel", json={"port_count": 12})
    assert resp.status_code == 409


def test_update_port_label_and_status(client, rack_id):
    item = client.post(
        f"/racks/{rack_id}/items",
        json={"name": "Patch Panel", "equipment_type": "patch_panel", "start_u": 1, "size_u": 1},
    ).json()
    panel = client.post(f"/racks/{rack_id}/items/{item['id']}/patch-panel", json={"port_count": 4}).json()
    port_id = panel["ports"][0]["id"]

    resp = client.patch(
        f"/patch-panels/{panel['id']}/ports/{port_id}",
        json={"label": "Room 101 - Drop 3", "status": "patched"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["label"] == "Room 101 - Drop 3"
    assert body["status"] == "patched"
