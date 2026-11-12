def test_create_client(client):
    response = client.post("/clients/", json={
        "name": "Acme Corp",
        "industry": "Technology",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Acme Corp"
    assert data["industry"] == "Technology"
    assert data["id"] is not None


def test_create_client_missing_fields(client):
    response = client.post("/clients/", json={})
    assert response.status_code == 422


def test_create_client_empty_name(client):
    response = client.post("/clients/", json={"name": "", "industry": "Tech"})
    assert response.status_code == 422


def test_list_clients(client, sample_client):
    response = client.get("/clients/")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_client(client, sample_client):
    response = client.get(f"/clients/{sample_client['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Corp"


def test_get_client_not_found(client):
    response = client.get("/clients/999")
    assert response.status_code == 404
    assert "detail" in response.json()


def test_update_client(client, sample_client):
    response = client.put(f"/clients/{sample_client['id']}", json={
        "name": "Updated Corp",
    })
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Corp"
    assert response.json()["industry"] == "Technology"


def test_update_client_not_found(client):
    response = client.put("/clients/999", json={"name": "Ghost"})
    assert response.status_code == 404


def test_delete_client(client, sample_client):
    response = client.delete(f"/clients/{sample_client['id']}")
    assert response.status_code == 204

    response = client.get(f"/clients/{sample_client['id']}")
    assert response.status_code == 404


def test_delete_client_not_found(client):
    response = client.delete("/clients/999")
    assert response.status_code == 404
