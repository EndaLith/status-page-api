def test_create_service(client):
    response=client.post(
        "/services",
        json={"name":"A","description":"first","url":"http://a.com"},)
    assert response.status_code==201
    assert response.json()["name"]=="A"

