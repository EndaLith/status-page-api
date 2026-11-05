def create_service(client, admin_header, name="A"):
    response = client.post(
        "/services",
        json={"name": name, "description": "d", "url": "http://x.com"},
        headers=admin_header,
    )
    return response.json()["id"]


def test_create_health_check(client, admin_header):
    service_id = create_service(client, admin_header)
    response = client.post(
        f"/services/{service_id}/health_checks",
        json={"is_up": True, "response_ms": 120},
        headers=admin_header,
    )
    assert response.status_code == 201
    assert response.json()["is_up"] is True
    assert response.json()["response_ms"] == 120


def test_create_health_check_unknown_service(client, admin_header):
    response = client.post(
        "/services/999/health_checks",
        json={"is_up": True},
        headers=admin_header,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Service not found"


def test_create_health_check_requires_token(client, admin_header):
    service_id = create_service(client, admin_header)
    response = client.post(
        f"/services/{service_id}/health_checks", json={"is_up": True}
    )
    assert response.status_code == 401


def test_list_health_checks_newest_first(client, admin_header):
    service_id = create_service(client, admin_header)
    url = f"/services/{service_id}/health_checks"
    client.post(url, json={"is_up": True, "message": "first"}, headers=admin_header)
    client.post(url, json={"is_up": False, "message": "second"}, headers=admin_header)

    response = client.get(url)
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["message"] == "second"


def test_list_health_checks_limit_and_offset(client, admin_header):
    service_id = create_service(client, admin_header)
    url = f"/services/{service_id}/health_checks"
    client.post(url, json={"is_up": True, "message": "first"}, headers=admin_header)
    client.post(url, json={"is_up": False, "message": "second"}, headers=admin_header)

    page_one = client.get(url, params={"limit": 1})
    page_two = client.get(url, params={"limit": 1, "offset": 1})
    assert page_one.json()[0]["message"] == "second"
    assert page_two.json()[0]["message"] == "first"


def test_list_health_checks_invalid_limit(client, admin_header):
    service_id = create_service(client, admin_header)
    response = client.get(f"/services/{service_id}/health_checks", params={"limit": 0})
    assert response.status_code == 422


def test_list_health_checks_time_filters(client, admin_header):
    service_id = create_service(client, admin_header)
    url = f"/services/{service_id}/health_checks"
    client.post(url, json={"is_up": True}, headers=admin_header)
    client.post(url, json={"is_up": False}, headers=admin_header)

    after_all = client.get(url, params={"since": "2099-01-01T00:00:00Z"})
    before_all = client.get(url, params={"until": "2000-01-01T00:00:00Z"})
    since_old = client.get(url, params={"since": "2000-01-01T00:00:00Z"})
    until_future = client.get(url, params={"until": "2099-01-01T00:00:00Z"})

    assert after_all.json() == []
    assert before_all.json() == []
    assert len(since_old.json()) == 2
    assert len(until_future.json()) == 2
