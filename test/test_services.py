def test_create_service(client, admin_header):
    response = client.post(
        "/services",
        json={"name": "A", "description": "first", "url": "http://a.com"},
        headers=admin_header,
    )
    assert response.status_code == 201
    assert response.json()["name"] == "A"


def test_dublicate_name_return_conflict(client, admin_header):
    data = {"name": "A", "description": "first", "url": "https://a.com"}
    client.post(
        "/services",
        json=data,
        headers=admin_header,
    )
    response = client.post("/services", json=data, headers=admin_header)
    assert response.status_code == 409


def test_update_unknown_service_returns_not_found(client, admin_header):
    data = {"name": "C", "description": "third", "url": "https://c.com"}
    response = client.put(
        "/services/7",
        json=data,
        headers=admin_header,
    )
    assert response.status_code == 404


def test_archived_services_is_hidden(client, admin_header):
    created = client.post(
        "/services",
        json={"name": "B", "description": "second", "url": "https://b.com"},
        headers=admin_header,
    )
    assert created.status_code == 201, created.json()
    service_id = created.json()["id"]
    delete_response = client.delete(f"/services/{service_id}", headers=admin_header)
    assert delete_response.status_code == 204
    assert client.get(f"/services/{service_id}").status_code == 404
    assert client.get("/services").json() == []


def test_archive_only_affects_requested_service(client, admin_header):
    a = client.post(
        "/services",
        json={"name": "A", "description": "first", "url": "http://a.com"},
        headers=admin_header,
    )
    b = client.post(
        "/services",
        json={"name": "B", "description": "second", "url": "http://b.com"},
        headers=admin_header,
    )
    a_id = a.json()["id"]
    b_id = b.json()["id"]

    delete_response = client.delete(f"/services/{b_id}", headers=admin_header)
    assert delete_response.status_code == 204
    assert client.get(f"/services/{b_id}").status_code == 404
    assert client.get(f"/services/{a_id}").status_code == 200


def test_user_cannot_create_service(client):
    client.post("/auth/register", json={"username": "bob", "password": "secret123"})
    login = client.post(
        "/auth/login", data={"username": "bob", "password": "secret123"}
    )
    token = login.json()["access_token"]
    response = client.post(
        "/services",
        json={"name": "X", "description": "x", "url": "http://x.com"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_create_service_without_token(client):
    response = client.post(
        "/services",
        json={"name": "Y", "description": "y", "url": "http://y.com"},
    )
    assert response.status_code == 401
