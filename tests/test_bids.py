def test_create_bid(client, sample_client):
    response = client.post("/bids/", json={
        "client_id": sample_client["id"],
        "title": "New Project",
        "value": 100000,
        "estimated_cost": 70000,
        "deadline": "2027-01-15",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Project"
    assert data["status"] == "draft"


def test_create_bid_unknown_client(client):
    response = client.post("/bids/", json={
        "client_id": 999,
        "title": "Ghost Bid",
        "value": 10000,
        "estimated_cost": 5000,
        "deadline": "2026-12-01",
    })
    assert response.status_code == 404
    assert "Client" in response.json()["detail"]


def test_create_bid_negative_value(client, sample_client):
    response = client.post("/bids/", json={
        "client_id": sample_client["id"],
        "title": "Bad Bid",
        "value": -100,
        "estimated_cost": 50,
        "deadline": "2026-12-01",
    })
    assert response.status_code == 422


def test_create_bid_missing_title(client, sample_client):
    response = client.post("/bids/", json={
        "client_id": sample_client["id"],
        "value": 10000,
        "estimated_cost": 5000,
        "deadline": "2026-12-01",
    })
    assert response.status_code == 422


def test_list_bids(client, sample_bid):
    response = client.get("/bids/")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_list_bids_filter_by_status(client, sample_bid):
    response = client.get("/bids/?status=draft")
    assert response.status_code == 200
    for bid in response.json():
        assert bid["status"] == "draft"


def test_list_bids_filter_by_client(client, sample_bid):
    response = client.get(f"/bids/?client_id={sample_bid['client_id']}")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_bid(client, sample_bid):
    response = client.get(f"/bids/{sample_bid['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == "Test Project"


def test_get_bid_not_found(client):
    response = client.get("/bids/999")
    assert response.status_code == 404
    assert "detail" in response.json()


def test_update_bid(client, sample_bid):
    response = client.put(f"/bids/{sample_bid['id']}", json={
        "title": "Updated Project",
        "status": "submitted",
    })
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Project"
    assert response.json()["status"] == "submitted"
    assert response.json()["value"] == 50000.0


def test_update_bid_not_found(client):
    response = client.put("/bids/999", json={"title": "Ghost"})
    assert response.status_code == 404


def test_update_bid_invalid_status(client, sample_bid):
    response = client.put(f"/bids/{sample_bid['id']}", json={
        "status": "invalid_status",
    })
    assert response.status_code == 422


def test_delete_bid(client, sample_bid):
    response = client.delete(f"/bids/{sample_bid['id']}")
    assert response.status_code == 204

    response = client.get(f"/bids/{sample_bid['id']}")
    assert response.status_code == 404


def test_delete_bid_not_found(client):
    response = client.delete("/bids/999")
    assert response.status_code == 404
