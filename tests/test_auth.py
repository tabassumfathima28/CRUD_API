from types import SimpleNamespace
from unittest.mock import Mock

from fastapi.testclient import TestClient
from supabase_auth.errors import AuthApiError, AuthInvalidCredentialsError

from conftest import app
from supabase_client import supabase


client = TestClient(app)


def _auth_response():
    return SimpleNamespace(
        user=SimpleNamespace(
            id="user-123",
            email="person@example.com",
            created_at="2025-01-02T03:04:05Z",
        ),
        session=SimpleNamespace(
            access_token="access-token",
            refresh_token="refresh-token",
        ),
    )


def test_signup_returns_created_user_and_tokens(monkeypatch):
    sign_up = Mock(return_value=_auth_response())
    monkeypatch.setattr(supabase.auth, "sign_up", sign_up)

    response = client.post(
        "/auth/signup",
        json={"email": "person@example.com", "password": "valid-password"},
    )

    assert response.status_code == 201
    assert response.json()["access_token"] == "access-token"
    assert response.json()["refresh_token"] == "refresh-token"
    assert response.json()["user"]["id"] == "user-123"
    sign_up.assert_called_once()


def test_login_returns_created_tokens(monkeypatch):
    sign_in = Mock(return_value=_auth_response())
    monkeypatch.setattr(supabase.auth, "sign_in_with_password", sign_in)

    response = client.post(
        "/auth/login",
        json={"email": "person@example.com", "password": "valid-password"},
    )

    assert response.status_code == 200
    assert response.json()["access_token"] == "access-token"
    assert response.json()["refresh_token"] == "refresh-token"
    sign_in.assert_called_once()


def test_auth_endpoints_reject_missing_fields():
    assert client.post("/auth/signup", json={"email": "person@example.com"}).status_code == 400
    assert client.post("/auth/login", json={"password": "valid-password"}).status_code == 400


def test_login_rejects_invalid_credentials(monkeypatch):
    sign_in = Mock(side_effect=AuthInvalidCredentialsError("invalid"))
    monkeypatch.setattr(supabase.auth, "sign_in_with_password", sign_in)

    response = client.post(
        "/auth/login",
        json={"email": "person@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"]["error"] == "Invalid email or password"


def test_public_info_is_accessible_without_authentication():
    response = client.get("/public/info")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome stranger! This info is public."
    }


def test_profile_requires_a_well_formed_bearer_header():
    for headers in ({}, {"Authorization": "Basic token"}, {"Authorization": "Bearer"}):
        response = client.get("/protected/profile", headers=headers)

        assert response.status_code == 401
        assert response.json() == {"error": "Access token required"}


def test_profile_returns_verified_user_info(monkeypatch):
    user = SimpleNamespace(
        id="user-123",
        email="person@example.com",
        created_at="2025-01-02T03:04:05Z",
        password="must-not-be-returned",
    )
    get_user = Mock(return_value=SimpleNamespace(user=user))
    monkeypatch.setattr(supabase.auth, "get_user", get_user)

    response = client.get(
        "/protected/profile",
        headers={"Authorization": "Bearer verified-token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": "user-123",
        "email": "person@example.com",
        "created_at": "2025-01-02T03:04:05Z",
    }
    get_user.assert_called_once_with("verified-token")


def test_profile_rejects_tampered_token(monkeypatch):
    get_user = Mock(side_effect=AuthApiError("invalid token", 401, None))
    monkeypatch.setattr(supabase.auth, "get_user", get_user)

    response = client.get(
        "/protected/profile",
        headers={"Authorization": "Bearer tampered-token"},
    )

    assert response.status_code == 401
    assert response.json() == {"error": "Invalid or expired token"}
    get_user.assert_called_once_with("tampered-token")


def test_dashboard_requires_authentication():
    response = client.get("/protected/dashboard")

    assert response.status_code == 401
    assert response.json() == {"error": "Access token required"}


def test_dashboard_injects_verified_user(monkeypatch):
    user = SimpleNamespace(
        id="user-123",
        email="person@example.com",
        created_at="2025-01-02T03:04:05Z",
    )
    monkeypatch.setattr(
        supabase.auth,
        "get_user",
        Mock(return_value=SimpleNamespace(user=user)),
    )

    response = client.get(
        "/protected/dashboard",
        headers={"Authorization": "Bearer verified-token"},
    )

    assert response.status_code == 200
    assert response.json()["user"]["id"] == "user-123"


def test_logout_revokes_verified_token_without_shared_session(monkeypatch):
    user = SimpleNamespace(
        id="user-123",
        email="person@example.com",
        created_at="2025-01-02T03:04:05Z",
    )
    get_user = Mock(return_value=SimpleNamespace(user=user))
    sign_out = Mock()
    monkeypatch.setattr(supabase.auth, "get_user", get_user)
    monkeypatch.setattr(supabase.auth.admin, "sign_out", sign_out)

    response = client.post(
        "/auth/logout",
        headers={"Authorization": "Bearer verified-token"},
    )

    assert response.status_code == 204
    assert response.content == b""
    sign_out.assert_called_once_with("verified-token", scope="global")


def test_logout_rejects_missing_or_invalid_tokens(monkeypatch):
    missing_response = client.post("/auth/logout")
    assert missing_response.status_code == 401
    assert missing_response.json() == {"error": "Access token required"}

    monkeypatch.setattr(
        supabase.auth,
        "get_user",
        Mock(side_effect=AuthApiError("invalid token", 401, None)),
    )
    sign_out = Mock()
    monkeypatch.setattr(supabase.auth.admin, "sign_out", sign_out)

    invalid_response = client.post(
        "/auth/logout",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert invalid_response.status_code == 401
    assert invalid_response.json() == {"error": "Invalid or expired token"}
    sign_out.assert_not_called()


def test_openapi_documents_bearer_auth_only_for_protected_routes():
    schema = app.openapi()
    paths = schema["paths"]
    security_schemes = schema["components"]["securitySchemes"]

    assert security_schemes["SupabaseAccessToken"] == {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Use the access_token returned by /auth/login.",
    }
    assert paths["/protected/profile"]["get"]["security"] == [
        {"SupabaseAccessToken": []}
    ]
    assert paths["/protected/dashboard"]["get"]["security"] == [
        {"SupabaseAccessToken": []}
    ]
    assert paths["/auth/logout"]["post"]["security"] == [
        {"SupabaseAccessToken": []}
    ]
    assert "security" not in paths["/public/info"]["get"]
    assert "security" not in paths["/auth/login"]["post"]
