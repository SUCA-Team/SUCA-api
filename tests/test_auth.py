"""Tests for authentication with Firebase."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


@patch("src.suca.api.v1.endpoints.auth.verify_firebase_token")
def test_verify_token_success(mock_verify: MagicMock, client: TestClient):
    """Test successful Firebase token verification."""
    # Mock Firebase token verification
    mock_verify.return_value = {
        "uid": "test_user_123",
        "email": "test@example.com",
        "email_verified": True,
        "name": "Test User",
        "picture": "https://example.com/photo.jpg",
    }

    response = client.post(
        "/api/v1/auth/verify",
        json={"id_token": "mock_firebase_token"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["user_id"] == "test_user_123"
    assert data["email"] == "test@example.com"
    assert data["email_verified"] is True
    assert data["display_name"] == "Test User"
    assert data["photo_url"] == "https://example.com/photo.jpg"


@patch("src.suca.api.v1.endpoints.auth.verify_firebase_token")
def test_verify_token_invalid(mock_verify: MagicMock, client: TestClient):
    """Test Firebase token verification with invalid token."""
    from fastapi import HTTPException, status

    # Mock Firebase token verification failure
    mock_verify.side_effect = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication token",
    )

    response = client.post(
        "/api/v1/auth/verify",
        json={"id_token": "invalid_token"},
    )

    assert response.status_code == 401
    assert "Invalid" in response.json()["detail"]


def test_get_current_user(client: TestClient, auth_headers: dict):
    """Test getting current user info with valid token."""
    response = client.get("/api/v1/auth/me", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Should return user_id from custom JWT (for backward compatibility)
    assert "user_id" in data


def test_get_current_user_no_token(client: TestClient):
    """Test getting current user without token."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 403


def test_get_current_user_invalid_token(client: TestClient):
    """Test getting current user with invalid token."""
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401


def test_refresh_token(client: TestClient, auth_headers: dict):
    """Test token refresh endpoint."""
    response = client.post("/api/v1/auth/refresh", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "user_id" in data
    assert "message" in data


def test_refresh_token_no_auth(client: TestClient):
    """Test refresh endpoint without authentication."""
    response = client.post("/api/v1/auth/refresh")
    assert response.status_code == 403
