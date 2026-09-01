"""
Tests for the real cookie-based JWT auth added on Day 8, plus a couple of
tests confirming the dev-only X-User-Id fallback's production lockout
actually works (not just documented).
"""

from starlette.testclient import TestClient

import app.main as main_module
from app.core.config import get_settings


def register(client, email="alice@example.com", password="hunter22", full_name="Alice"):
    return client.post("/auth/register", json={"email": email, "password": password, "full_name": full_name})


def test_register_creates_user_and_sets_cookies(client):
    r = register(client)
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "alice@example.com"
    assert "password" not in body and "password_hash" not in body
    assert "access_token" in client.cookies
    assert "refresh_token" in client.cookies


def test_register_duplicate_email_conflicts(client):
    register(client)
    r = register(client)
    assert r.status_code == 409


def test_login_with_correct_password_succeeds(client):
    register(client, password="correct-horse")
    client.cookies.clear()
    r = client.post("/auth/login", json={"email": "alice@example.com", "password": "correct-horse"})
    assert r.status_code == 200
    assert "access_token" in client.cookies


def test_login_with_wrong_password_401(client):
    register(client, password="correct-horse")
    client.cookies.clear()
    r = client.post("/auth/login", json={"email": "alice@example.com", "password": "wrong-password"})
    assert r.status_code == 401


def test_login_unknown_email_401_same_as_wrong_password(client):
    r = client.post("/auth/login", json={"email": "nobody@example.com", "password": "whatever123"})
    assert r.status_code == 401
    # Same message for "no such user" and "wrong password" - shouldn't be
    # possible to tell which one happened from the response.
    wrong_pw_detail = client.post(
        "/auth/login", json={"email": "nobody@example.com", "password": "whatever123"}
    ).json()["detail"]
    assert r.json()["detail"] == wrong_pw_detail


def test_me_requires_authentication(client):
    r = client.get("/auth/me")
    assert r.status_code == 401


def test_me_returns_current_user_after_login(client):
    register(client, email="bob@example.com", full_name="Bob")
    r = client.get("/auth/me")
    assert r.status_code == 200
    assert r.json()["email"] == "bob@example.com"
    assert r.json()["full_name"] == "Bob"


def test_authenticated_requests_work_end_to_end(client):
    """Register, then use the resulting session cookie for a real protected endpoint, not just /auth/me."""
    register(client, email="carol@example.com")
    r = client.post("/folders", json={"name": "My Folder"})
    assert r.status_code == 201


def test_refresh_issues_a_working_new_session(client):
    register(client)
    old_access = client.cookies.get("access_token")

    r = client.post("/auth/refresh")
    assert r.status_code == 200
    assert client.cookies.get("access_token") != old_access

    # New cookie actually works for a protected endpoint.
    assert client.get("/auth/me").status_code == 200


def test_refresh_without_a_refresh_cookie_401(client):
    r = client.post("/auth/refresh")
    assert r.status_code == 401


def test_logout_clears_session_and_blocks_further_requests(client):
    register(client)
    assert client.get("/auth/me").status_code == 200

    r = client.post("/auth/logout")
    assert r.status_code == 204

    assert client.get("/auth/me").status_code == 401


def test_access_token_cannot_be_used_as_a_refresh_token(client):
    """The access cookie is scoped path=/ so it WOULD be sent to /auth/refresh by a real browser
    if it were the only cookie - but /auth/refresh must reject it because it's the wrong token type."""
    register(client)
    access_token = client.cookies.get("access_token")

    client.cookies.clear()
    client.cookies.set("refresh_token", access_token)
    r = client.post("/auth/refresh")
    assert r.status_code == 401


def test_x_user_id_header_still_works_as_dev_fallback(client, make_user):
    """Backward compatibility check: the temporary header auth used by all the Day 3-7 tests must keep working in dev."""
    _, headers = make_user("dave@example.com")
    r = client.get("/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == "dave@example.com"


def test_x_user_id_header_is_rejected_in_production(client, make_user, monkeypatch):
    """The dev-only fallback must be a hard no-op in production, not just discouraged in a comment."""
    _, headers = make_user("eve@example.com")

    prod_settings = get_settings()
    monkeypatch.setattr(prod_settings, "ENV", "production")

    r = client.get("/auth/me", headers=headers)
    assert r.status_code == 401


def test_second_independent_login_session_does_not_leak_into_first(db_session):
    """Two separate browser sessions (two TestClients sharing the same app+db) must not see each other's cookies."""
    from app.core.database import get_db

    def override_get_db():
        yield db_session

    main_module.app.dependency_overrides[get_db] = override_get_db
    try:
        client_a = TestClient(main_module.app)
        client_b = TestClient(main_module.app)

        register(client_a, email="userA@example.com")
        register(client_b, email="userB@example.com")

        assert client_a.get("/auth/me").json()["email"] == "userA@example.com"
        assert client_b.get("/auth/me").json()["email"] == "userB@example.com"
    finally:
        main_module.app.dependency_overrides.clear()
