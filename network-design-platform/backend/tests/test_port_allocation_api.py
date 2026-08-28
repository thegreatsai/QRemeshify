def test_calculate_endpoint(client):
    resp = client.post(
        "/port-allocation/calculate",
        json={"data_drops": 90, "ports_per_switch": 48, "uplink_ports_per_switch": 2},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["switches_needed"] == 2
    assert sum(p["data_ports"] for p in body["per_switch"]) == 90


def test_calculate_endpoint_invalid_input_returns_422(client):
    resp = client.post("/port-allocation/calculate", json={"data_drops": 5, "ap_drops": 5, "ap_reserved_ports_per_switch": 0})
    assert resp.status_code == 422
    assert "ap_reserved_ports_per_switch" in resp.json()["detail"]
