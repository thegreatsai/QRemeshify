def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_create_and_list_site(client):
    payload = {"building_code": "27Q273", "rack_id": "MDF-1", "name": "PS 273", "district": "27"}
    resp = client.post("/sites", json=payload)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["building_code"] == "27Q273"
    assert body["workflow_stage"] == "survey"

    resp = client.get("/sites")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_duplicate_building_code_rejected(client):
    payload = {"building_code": "27Q273", "name": "PS 273"}
    assert client.post("/sites", json=payload).status_code == 201
    resp = client.post("/sites", json=payload)
    assert resp.status_code == 409


def test_reference_list_roundtrip(client):
    resp = client.post("/reference-lists", json={"key": "cable_type", "label": "Cable Type"})
    assert resp.status_code == 201

    resp = client.post(
        "/reference-lists/cable_type/items",
        json={"value": "CAT5E", "label": "CAT5E", "sort_order": 1},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["value"] == "CAT5E"


def test_room_and_rack_under_site(client):
    site = client.post("/sites", json={"building_code": "30Q149", "name": "PS 149"}).json()
    site_id = site["id"]

    resp = client.post(f"/sites/{site_id}/rooms", json={"name": "MDF", "room_type_value": "MDF"})
    assert resp.status_code == 201
    assert resp.json()["site_id"] == site_id

    resp = client.post(f"/sites/{site_id}/racks", json={"rack_number": "Rack 1"})
    assert resp.status_code == 201
    assert resp.json()["site_id"] == site_id


def test_room_under_missing_site_404(client):
    resp = client.post("/sites/999/rooms", json={"name": "MDF"})
    assert resp.status_code == 404
