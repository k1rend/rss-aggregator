"""Tests for /api/auth/signup and /api/auth/signin."""

import uuid

from conftest import PASSWORD


def unique_login(prefix="auth"):
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def test_signup_creates_user_and_returns_token(client):
    login = unique_login()

    response = client.post("/api/auth/signup", json={"login": login, "password": PASSWORD})

    assert response.status_code == 201
    body = response.json()
    assert body["user"] == {"id": body["user"]["id"], "login": login}
    assert isinstance(body["user"]["id"], int)
    assert isinstance(body["token"], str) and body["token"]

    # the token is immediately usable
    me = client.get("/api/articles", token=body["token"])
    assert me.status_code == 200


def test_signup_rejects_duplicate_login(client):
    login = unique_login("dup")
    assert client.post("/api/auth/signup", json={"login": login, "password": PASSWORD}).status_code == 201

    response = client.post("/api/auth/signup", json={"login": login, "password": "other-pass"})

    assert response.status_code == 409
    assert response.json()["error"] == "login already taken"


def test_signup_requires_login_and_password(client):
    missing_password = client.post("/api/auth/signup", json={"login": unique_login()})
    missing_login = client.post("/api/auth/signup", json={"password": PASSWORD})
    empty_body = client.post("/api/auth/signup", json={})

    for response in (missing_password, missing_login, empty_body):
        assert response.status_code == 400
        assert "required" in response.json()["error"]


def test_signup_rejects_short_password(client):
    response = client.post("/api/auth/signup", json={"login": unique_login(), "password": "12345"})

    assert response.status_code == 400
    assert "at least 6" in response.json()["error"]


def test_signup_rejects_invalid_login(client):
    response = client.post("/api/auth/signup", json={"login": "no spaces allowed", "password": PASSWORD})

    assert response.status_code == 400
    assert "login must be" in response.json()["error"]


def test_signin_returns_working_token(client, user):
    response = client.post("/api/auth/signin", json={"login": user.login, "password": user.password})

    assert response.status_code == 200
    body = response.json()
    assert body["user"] == {"id": user.id, "login": user.login}
    assert body["token"]

    history = client.get("/api/history", token=body["token"])
    assert history.status_code == 200


def test_signin_with_wrong_password(client, user):
    response = client.post("/api/auth/signin", json={"login": user.login, "password": "wrong-password"})

    assert response.status_code == 401
    assert response.json()["error"] == "Invalid login or password"


def test_signin_with_unknown_user(client):
    response = client.post("/api/auth/signin", json={"login": unique_login("ghost"), "password": PASSWORD})

    assert response.status_code == 401
    assert response.json()["error"] == "Invalid login or password"


def test_signin_requires_both_fields(client):
    response = client.post("/api/auth/signin", json={"login": "someone"})

    assert response.status_code == 400
    assert "required" in response.json()["error"]


def test_protected_endpoints_require_token(client):
    for path in ("/api/feeds", "/api/feeds/1", "/api/articles", "/api/articles/1", "/api/history"):
        response = client.get(path)
        assert response.status_code == 401, path
        assert response.json()["error"] == "Missing Authorization header"

    view = client.post("/api/articles/1/view")
    assert view.status_code == 401


def test_invalid_token_is_rejected(client):
    response = client.get("/api/articles", token="not-a-real-token")

    assert response.status_code == 401
    assert response.json()["error"] == "Invalid or expired token"
