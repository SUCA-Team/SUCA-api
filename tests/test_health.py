"""Tests for health endpoint."""

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    """Test health endpoint returns proper response."""
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert "success" in data
    assert "data" in data

    # Check health data structure
    health_data = data["data"]
    assert "status" in health_data
    assert "timestamp" in health_data
    assert "version" in health_data
    assert "database_status" in health_data
    assert "uptime" in health_data

    # Check that basic fields are not empty
    assert health_data["status"] in ["healthy", "degraded", "unhealthy"]
    assert health_data["version"] is not None
