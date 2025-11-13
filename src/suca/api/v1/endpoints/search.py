"""Search endpoints for dictionary operations."""

from fastapi import APIRouter, Query

from ....api.deps import SearchServiceDep
from ....schemas.search import SearchRequest, SearchResponse
from ....core.exceptions import SearchException, HTTPExceptions

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("", response_model=SearchResponse)
def search(
    search_service: SearchServiceDep,
    q: str = Query(..., description="Search query", min_length=1),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum results to return"),
    include_rare: bool = Query(default=False, description="Include rare/uncommon words")
) -> SearchResponse:
    """
    Search dictionary entries with intelligent prioritization:
    1. Exact matches (行 = 行)
    2. Common words starting with query (行 → 行く, 行き)  
    3. Common words containing query (行 → 銀行, 旅行)
    4. All other partial matches
    """
    try:
        # Create search request
        search_request = SearchRequest(
            query=q,
            limit=limit,
            include_rare=include_rare
        )
        
        # Use search service
        return search_service.search_entries(search_request)
        
    except SearchException as e:
        raise HTTPExceptions.bad_request(detail=e.message)
    except Exception as e:
        raise HTTPExceptions.internal_server_error(detail="Search failed")
