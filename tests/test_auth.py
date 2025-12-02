"""Tests for authentication."""

from fastapi.testclient import TestClient


def test_login_success(client: TestClient):
    """Test successful login with demo user."""
    response = client.post(
        "/api/v1/auth/login", json={"username": "demo_user", "password": "password123"}
    )

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 1800


def test_login_wrong_password(client: TestClient):
    """Test login with wrong password."""
    response = client.post(
        "/api/v1/auth/login", json={"username": "demo_user", "password": "wrongpassword"}
    )

    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


def test_login_nonexistent_user(client: TestClient):
    """Test login with non-existent user."""
    response = client.post(
        "/api/v1/auth/login", json={"username": "nonexistent", "password": "password"}
    )

    assert response.status_code == 401


def test_register_new_user(client: TestClient):
    """Test registering a new user."""
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "testuser", "email": "test@example.com", "password": "testpassword123"},
    )

    assert response.status_code == 201
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_username(client: TestClient):
    """Test registering with existing username."""
    # Register first user
    client.post(
        "/api/v1/auth/register",
        json={"username": "testuser2", "email": "test1@example.com", "password": "password123"},
    )

    # Try to register again with same username
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "testuser2", "email": "test2@example.com", "password": "password123"},
    )

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_get_current_user(client: TestClient, auth_headers: dict):
    """Test getting current user info."""
    response = client.get("/api/v1/auth/me", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert data["user_id"] == "demo_user"
    assert data["username"] == "demo_user"
    assert data["email"] == "demo@example.com"


def test_get_current_user_no_token(client: TestClient):
    """Test getting current user without token."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 403


def test_get_current_user_invalid_token(client: TestClient):
    """Test getting current user with invalid token."""
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401
