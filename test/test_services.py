def test_create_service(client):
    response = client.post(
        "/services",
        json={"name": "A", "description": "first", "url": "http://a.com"},
    )
    assert response.status_code == 201
    assert response.json()["name"] == "A"


def test_dublicate_name_return_conflict(client):
    data = {"name": "A", "description": "first", "url": "https://a.com"}
    client.post("/services", json=data)
    response = client.post("/services", json=data)
    assert response.status_code == 409


def test_update_unknown_service_returns_not_found(client):
    data = {"name": "C", "description": "third", "url": "https://c.com"}
    response = client.put("/services/7", json=data)
    assert response.status_code == 404


def test_archived_services_is_hidden(client):
    created = client.post(
        "/services",
        json={"name": "B", "description": "second", "url": "https://b.com"},
    )
    assert created.status_code == 201, created.json()
    service_id = created.json()["id"]
    client.delete(f"/services/{service_id}")
    assert client.get(f"/services/{service_id}").status_code == 404
    assert client.get("/services").json() == []


def test_archive_only_affects_requested_service(client):
    a = client.post(
        "/services",
        json={"name": "A", "description": "first", "url": "http://a.com"},
    )
    b = client.post(
        "/services",
        json={"name": "B", "description": "second", "url": "http://b.com"},
    )
    a_id = a.json()["id"]
    b_id = b.json()["id"]

    client.delete(f"/services/{b_id}")

    assert client.get(f"/services/{b_id}").status_code == 404
    assert client.get(f"/services/{a_id}").status_code == 200
