def create_service(client, admin_header, name="A"):
    response = client.post(
        "/services",
        json={"name": name, "description": "d", "url": "http://x.com"},
        headers=admin_header,
    )
    return response.json()["id"]


def maintenance_body(
    service_id, start="2099-01-01T02:00:00Z", end="2099-01-01T04:00:00Z"
):
    return {
        "service_id": service_id,
        "title": "DB upgrade",
        "description": "Planned",
        "started_at": start,
        "ended_at": end,
    }


def test_create_maintenance(client, admin_header):
    service_id = create_service(client, admin_header)
    response = client.post(
        "/maintenance-windows", json=maintenance_body(service_id), headers=admin_header
    )
    assert response.status_code == 201
    assert response.json()["title"] == "DB upgrade"


def test_maintenance_end_before_start(client, admin_header):
    service_id = create_service(client, admin_header)
    body = maintenance_body(
        service_id, start="2099-01-01T04:00:00Z", end="2099-01-01T02:00:00Z"
    )
    response = client.post("/maintenance-windows", json=body, headers=admin_header)
    assert response.status_code == 422


def test_maintenance_unknown_service(client, admin_header):
    response = client.post(
        "/maintenance-windows", json=maintenance_body(999), headers=admin_header
    )
    assert response.status_code == 404


def test_maintenance_requires_admin(client, admin_header):
    service_id = create_service(client, admin_header)
    client.post("/auth/register", json={"username": "bob", "password": "secret123"})
    token = client.post(
        "/auth/login", data={"username": "bob", "password": "secret123"}
    ).json()["access_token"]
    as_user = client.post(
        "/maintenance-windows",
        json={"Authorization": f"Bearer {token}"},
    )
    no_token = client.post("/maintenance-windows", json=maintenance_body(service_id))
    assert as_user.status_code == 401
    assert no_token.status_code == 401


def test_list_maintenance_is_public(client):
    response = client.get("/maintenance-windows")
    assert response.status_code == 200


def test_upcoming_filter(client, admin_header):
    service_id = create_service(client, admin_header)
    past = maintenance_body(
        service_id, start="2000-01-01T02:00:00Z", end="2000-01-01T04:00:00Z"
    )
    future = maintenance_body(service_id)
    client.post("/maintenance-windows", json=past, headers=admin_header)
    client.post("/maintenance-windows", json=future, headers=admin_header)

    everythink = client.get("/maintenance-windows").json()
    upcoming = client.get("/maintenance-windows", params={"upcoming": True}).json()
    assert len(everythink) == 2
    assert len(upcoming) == 1
