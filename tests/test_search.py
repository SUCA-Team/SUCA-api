"""Tests for search functionality."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from src.suca.schemas.search import SearchRequest
from src.suca.services.search_service import SearchService


def test_search_endpoint(client: TestClient):
    """Test search endpoint returns proper response format."""
    response = client.get("/api/v1/search?q=test")
    
    # Should return 404 for empty database or handle gracefully
    assert response.status_code in [200, 404]
    
    if response.status_code == 200:
        data = response.json()
        assert "results" in data
        assert "total_count" in data
        assert "success" in data


def test_search_service_empty_query(session: Session):
    """Test search service with empty query."""
    service = SearchService(session)
    
    with pytest.raises(Exception):  # Should raise SearchException
        service.search_entries(SearchRequest(query=""))


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
