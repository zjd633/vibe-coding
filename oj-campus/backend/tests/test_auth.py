from conftest import register


def test_register_normalizes_identity_and_sets_session(client):
    response = client.post(
        "/api/auth/register",
        json={
            "username": "Alice_1",
            "email": "ALICE@Example.COM",
            "display_name": "Alice",
            "password": "correct-horse-battery",
        },
    )

    assert response.status_code == 201
    assert response.json()["username"] == "alice_1"
    assert response.json()["email"] == "alice@example.com"
    assert "oj_session" in response.headers["set-cookie"]
    assert "httponly" in response.headers["set-cookie"].lower()


def test_registration_validation_returns_standard_error_shape(client):
    response = client.post(
        "/api/auth/register",
        json={
            "username": "!!",
            "email": "not-an-email",
            "display_name": "",
            "password": "short",
        },
    )

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"
    assert response.json()["message"]
    assert response.json()["field_errors"]


def test_framework_errors_use_the_standard_error_shape(client):
    response = client.get("/api/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {"code": "not_found", "message": "Not Found"}


def test_login_logout_and_expired_session(client):
    assert register(client).status_code == 201
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401

    response = client.post(
        "/api/auth/login", json={"username": "ALICE", "password": "correct-horse-battery"}
    )
    assert response.status_code == 200
    assert response.json()["username"] == "alice"
    assert client.get("/api/auth/me").status_code == 200

    from datetime import datetime, timezone

    from app.database import session_scope
    from app.models import Session

    with session_scope(client.app.state.database_url) as db:
        db.query(Session).update({Session.expires_at: datetime(2000, 1, 1, tzinfo=timezone.utc)})
        db.commit()
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json()["code"] == "authentication_required"
    with session_scope(client.app.state.database_url) as db:
        assert db.query(Session).count() == 0


def test_optional_session_probe_never_uses_an_authentication_error(client):
    anonymous = client.get("/api/auth/session")
    assert anonymous.status_code == 200
    assert anonymous.json() is None

    assert register(client).status_code == 201
    authenticated = client.get("/api/auth/session")
    assert authenticated.status_code == 200
    assert authenticated.json()["username"] == "alice"

    assert client.post("/api/auth/logout").status_code == 204
    signed_out = client.get("/api/auth/session")
    assert signed_out.status_code == 200
    assert signed_out.json() is None


def test_optional_session_probe_retires_an_expired_session(client):
    from datetime import datetime, timezone

    from app.database import session_scope
    from app.models import Session

    assert register(client).status_code == 201
    with session_scope(client.app.state.database_url) as db:
        db.query(Session).update({Session.expires_at: datetime(2000, 1, 1, tzinfo=timezone.utc)})
        db.commit()

    response = client.get("/api/auth/session")
    assert response.status_code == 200
    assert response.json() is None
    assert "oj_session=\"\"" in response.headers["set-cookie"]
    with session_scope(client.app.state.database_url) as db:
        assert db.query(Session).count() == 0


def test_unexpected_errors_are_standardized_without_internal_details(client):
    from fastapi.testclient import TestClient

    @client.app.get("/api/test-runtime-error")
    def test_runtime_error():
        raise RuntimeError("private diagnostic detail")

    with TestClient(client.app, raise_server_exceptions=False) as no_raise_client:
        response = no_raise_client.get("/api/test-runtime-error")

    assert response.status_code == 500
    assert response.json() == {"code": "internal_error", "message": "Internal server error"}


def test_concurrent_duplicate_registrations_return_a_standard_conflict(client):
    from concurrent.futures import ThreadPoolExecutor

    from fastapi.testclient import TestClient

    payload = {
        "username": "race_user",
        "email": "race@example.com",
        "display_name": "Race User",
        "password": "correct-horse-battery",
    }

    def register_once():
        with TestClient(client.app, raise_server_exceptions=False) as race_client:
            return race_client.post("/api/auth/register", json=payload)

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda _index: register_once(), range(2)))

    assert sorted(response.status_code for response in responses) == [201, 409]
    conflict = next(response for response in responses if response.status_code == 409)
    assert conflict.json()["code"] in {"registration_conflict", "username_taken", "email_taken"}


def test_logout_clears_the_session_cookie(client):
    assert register(client).status_code == 201

    response = client.post("/api/auth/logout")

    assert response.status_code == 204
    assert "oj_session=\"\"" in response.headers["set-cookie"]
    assert "max-age=0" in response.headers["set-cookie"].lower()


def test_profile_and_password_change_require_current_password(client):
    assert register(client).status_code == 201
    assert client.patch("/api/auth/profile", json={"display_name": "Alicia"}).json()["display_name"] == "Alicia"
    denied = client.patch(
        "/api/auth/password", json={"current_password": "wrong", "new_password": "new-correct-password"}
    )
    assert denied.status_code == 400
    assert denied.json()["code"] == "invalid_credentials"
    assert client.patch(
        "/api/auth/password",
        json={"current_password": "correct-horse-battery", "new_password": "new-correct-password"},
    ).status_code == 204
