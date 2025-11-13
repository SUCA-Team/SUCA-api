"""Schemas for the SUCA API."""

from .base import BaseResponse, ErrorResponse, PaginatedResponse
from .search import MeaningResponse, DictionaryEntryResponse, SearchResponse, SearchRequest
from .health import HealthStatus, HealthResponse

__all__ = [
    # Base
    "BaseResponse",
    "ErrorResponse", 
    "PaginatedResponse",
    
    # Search
    "MeaningResponse",
    "DictionaryEntryResponse", 
    "SearchResponse",
    "SearchRequest",
    
    # Health
    "HealthStatus",
    "HealthResponse",
]