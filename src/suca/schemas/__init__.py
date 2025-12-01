"""Schemas for the SUCA API."""

from .base import BaseResponse, ErrorResponse, PaginatedResponse
from .search import MeaningResponse, DictionaryEntryResponse, SearchResponse, SearchRequest
from .health import HealthStatus, HealthResponse
from .flashcard_schemas import (
    FlashcardBase,
    FlashcardCreate,
    FlashcardCreateNested,
    FlashcardUpdate,
    FlashcardResponse,
    DeckBase,
    DeckCreate,
    DeckUpdate,
    DeckResponse,
    FlashcardListResponse,
    DeckListResponse,
)

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
    
    # Flashcard
    "FlashcardBase",
    "FlashcardCreate",
    "FlashcardCreateNested",
    "FlashcardUpdate",
    "FlashcardResponse",
    "DeckBase",
    "DeckCreate",
    "DeckUpdate",
    "DeckResponse",
    "FlashcardListResponse",
    "DeckListResponse",
]