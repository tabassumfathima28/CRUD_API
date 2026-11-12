from types import SimpleNamespace
from unittest.mock import Mock

from fastapi.testclient import TestClient
from supabase_auth.errors import AuthInvalidCredentialsError

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
