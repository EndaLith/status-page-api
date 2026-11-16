def create_service(client, admin_header, name="A"):
    response = client.post(
        "/services",
        json={"name": name, "description": "d", "url": "http://x.com"},
        headers=admin_header,
    )

    return response.json()["id"]


def add_checks(client, admin_header, service_id, results):
    for is_up in results:
        client.post(
            f"/services/{service_id}/health_checks",
            json={"is_up": is_up},
            headers=admin_header,
        )


def test_uptime_percentage(client, admin_header):
    service_id = create_service(client, admin_header)
    add_checks(client, admin_header, service_id, [True, True, True, False])
    response = client.get(f"/services/{service_id}/uptime")
    assert response.status_code == 200
    body = response.json()
    assert body["total_checks"] == 4
    assert body["up_checks"] == 3
    assert body["uptime_percent"] == 75.0


def test_uptime_without_checks_is_null(client, admin_header):
    service_id = create_service(client, admin_header)
    response = client.get(f"/services/{service_id}/uptime")
    assert response.status_code == 200
    assert response.json()["total_checks"] == 0
    assert response.json()["uptime_percent"] is None


def test_uptime_unknown_service(client):
    response = client.get("/services/999/uptime")
    assert response.status_code == 404


def test_uptime_invalid_days(client, admin_header):
    service_id = create_service(client, admin_header)
    response = client.get(f"/services/{service_id}/uptime", params={"days": 0})
    assert response.status_code == 422


def test_uptime_default_days(client, admin_header):
    service_id = create_service(client, admin_header)
    response = client.get(f"/services/{service_id}/uptime")
    assert response.json()["days"] == 30


def test_uptime_ignores_other_services(client, admin_header):
    first = create_service(client, admin_header, "A")
    second = create_service(client, admin_header, "B")
    add_checks(client, admin_header, first, [True, True])
    add_checks(client, admin_header, second, [False, False])
    assert client.get(f"/services/{first}/uptime").json()["uptime_percent"] == 100.0
    assert client.get(f"/services/{second}/uptime").json()["uptime_percent"] == 0.0
