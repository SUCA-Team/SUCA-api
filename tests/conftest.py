"""Test configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from src.suca.api.deps import get_session
from src.suca.core.auth import create_access_token
from src.suca.main import app


@pytest.fixture(name="session")
def session_fixture():
    """Create a test database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create a test client with test database."""

    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="auth_headers")
def auth_headers_fixture():
    """Create authentication headers for testing."""
    # Create test token for demo_user
    access_token = create_access_token(data={"sub": "demo_user", "username": "demo_user"})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(name="auth_client")
def auth_client_fixture(client: TestClient, auth_headers: dict):
    """Create an authenticated test client."""
    # Store headers in client for convenience
    client.headers.update(auth_headers)
    return client
