"""Tests for search functionality."""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from src.suca.schemas.search import SearchRequest, SearchResponse


def test_search_endpoint(client: TestClient):
    """Test search endpoint returns proper response format."""
    # Mock the search service to avoid SQLite incompatibility
    mock_response = SearchResponse(
        results=[],
        total_count=0,
        query="test",
        message="Found 0 results for 'test' (English search)",
        success=True,
    )

    with patch("src.suca.api.v1.endpoints.search.SearchServiceDep"):
        mock_service = Mock()
        mock_service.search_entries.return_value = mock_response

        # Override dependency
        from src.suca.api.deps import get_search_service
        from src.suca.main import app

        def override_search_service():
            return mock_service

        app.dependency_overrides[get_search_service] = override_search_service

        response = client.get("/api/v1/search?q=test")

        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total_count" in data
    assert "success" in data
    assert isinstance(data["results"], list)
    assert isinstance(data["total_count"], int)


def test_search_service_empty_query(session: Session):
    """Test search service with empty query."""
    from pydantic import ValidationError

    # Empty query should fail at Pydantic validation level
    with pytest.raises(ValidationError):
        SearchRequest(query="")


def test_search_request_validation():
    """Test search request model validation."""
    # Valid request
    request = SearchRequest(query="test", limit=10, include_rare=False)
    assert request.query == "test"
    assert request.limit == 10
    assert request.include_rare is False

    # Test with minimum length validation
    with pytest.raises(ValueError):
        SearchRequest(query="", limit=10)
