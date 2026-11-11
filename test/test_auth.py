def register(client, username="bob", password="secret123"):
    return client.post(
        "/auth/register", json={"username": username, "password": password}
    )


def login(client, username="bob", password="secret123"):
    return client.post("/auth/login", data={"username": username, "password": password})


def test_register(client):
    response = register(client)
    assert response.status_code == 201
    assert response.json()["username"] == "bob"
    assert response.json()["role"] == "user"
    assert "password_hash" not in response.json()
    assert "password" not in response.json()


def test_register_duplicate_username(client):
    register(client)
    response = register(client)
    assert response.status_code == 409


def test_register_cannot_choose_role(client):
    response = client.post(
        "/auth/register",
        json={"username": "eve", "password": "secret123", "role": "admin"},
    )
    assert response.status_code == 201
    assert response.json()["role"] == "user"


def test_login_return_token(client):
    register(client)
    response = login(client)
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_wrong_password(client):
    register(client)
    responde = login(client, password="wrong")
    assert responde.status_code == 401
    assert responde.json()["detail"] == "Invalid username or password"


def test_login_unknown_user(client):
    response = login(client, username="nobody")
    assert response.status_code == 401


def test_me_with_token(client):
    register(client)
    token = login(client).json()["access_token"]
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["username"] == "bob"


def test_me_without_token(client):
    response = client.get("/auth/me")
    assert response.status_code == 401
