def create_service(client, admin_header, name="A"):
    response = client.post(
        "/services",
        json={"name": name, "description": "d", "url": "http://x.com"},
        headers=admin_header,
    )
    return response.json()["id"]


def create_incident(client, admin_header, service_ids):
    return client.post(
        "/incidents",
        json={
            "title": "Payment delays",
            "message": "Investigating",
            "service_ids": service_ids,
        },
        headers=admin_header,
    )


def test_create_incident(client, admin_header):
    service_id = create_service(client, admin_header)
    response = create_incident(client, admin_header, [service_id])
    assert response.status_code == 201
    assert response.json()["status"] == "investigating"
    assert response.json()["resolved_at"] is None


def test_create_incident_unknown_service_creates_nothing(client, admin_header):
    response = create_incident(client, admin_header, [999])
    assert response.status_code == 404
    assert client.get("/incidents").json() == []


def test_create_requires_services(client, admin_header):
    response = create_incident(client, admin_header, [])
    assert response.status_code == 422


def test_active_filter_excludes_resolved(client, admin_header):
    service_id = create_service(client, admin_header)
    first = create_incident(client, admin_header, [service_id]).json()["id"]
    second = create_incident(client, admin_header, [service_id])

    assert second.status_code == 201

    client.patch(
        f"/incidents/{first}/status",
        json={"status": "resolved", "message": "Fixed"},
        headers=admin_header,
    )

    all_incidents = client.get("/incidents").json()
    active = client.get("/incidents", params={"active": True}).json()
    assert len(all_incidents) == 2
    assert len(active) == 1


def test_resolved_then_reopen(client, admin_header):
    service_id = create_service(client, admin_header)
    incident_id = create_incident(client, admin_header, [service_id]).json()["id"]
    url = f"/incidents/{incident_id}/status"

    resolved = client.patch(
        url, json={"status": "resolved", "message": "Fixed"}, headers=admin_header
    )
    assert resolved.status_code == 200
    assert resolved.json()["resolved_at"] is not None

    reopened = client.patch(
        url,
        json={"status": "investigating", "message": "Back again"},
        headers=admin_header,
    )
    assert reopened.status_code == 200
    assert reopened.json()["resolved_at"] is None
    assert len(reopened.json()["updates"]) == 3


def test_invalid_transition_changes_nothing(client, admin_header):
    service_id = create_service(client, admin_header)
    incident_id = create_incident(client, admin_header, [service_id]).json()["id"]
    url = f"/incidents/{incident_id}/status"
    client.patch(
        url, json={"status": "resolved", "message": "Fixed"}, headers=admin_header
    )
    response = client.patch(
        url, json={"status": "monitoring", "message": "x"}, headers=admin_header
    )
    assert response.status_code == 400

    detail = client.get(f"/incidents/{incident_id}").json()
    assert detail["status"] == "resolved"
    assert len(detail["updates"]) == 2


def test_unknown_status_value_is_rejected(client, admin_header):
    service_id = create_service(client, admin_header)
    incident_id = create_incident(client, admin_header, [service_id]).json()["id"]
    response = client.patch(
        f"/incidents/{incident_id}/status",
        json={"status": "banana", "message": "x"},
        headers=admin_header,
    )
    assert response.status_code == 422


def test_change_status_requires_token(client, admin_header):
    service_id = create_service(client, admin_header)
    incident_id = create_incident(client, admin_header, [service_id]).json()["id"]
    response = client.patch(
        f"/incidents/{incident_id}/status",
        json={"status": "resolved", "message": "Fixed"},
    )
    assert response.status_code == 401
