def test_import_loads_data(client):
    response = client.post("/import")
    assert response.status_code == 200
    data = response.json()
    assert data["clients"]["imported"] > 0
    assert data["bids"]["imported"] > 0


def test_import_is_idempotent(client):
    client.post("/import")
    response = client.post("/import")
    data = response.json()
    assert data["clients"]["imported"] == 0
    assert data["clients"]["skipped"] > 0
    assert data["bids"]["imported"] == 0
    assert data["bids"]["skipped"] > 0


def test_import_reports_bad_rows(client):
    response = client.post("/import")
    data = response.json()
    assert len(data["bids"]["errors"]) > 0
