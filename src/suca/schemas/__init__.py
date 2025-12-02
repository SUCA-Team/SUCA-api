"""Schemas for the SUCA API."""

from .base import BaseResponse, ErrorResponse, PaginatedResponse
from .flashcard_schemas import (
    DeckBase,
    DeckCreate,
    DeckListResponse,
    DeckResponse,
    DeckUpdate,
    FlashcardBase,
    FlashcardCreate,
    FlashcardCreateNested,
    FlashcardListResponse,
    FlashcardResponse,
    FlashcardUpdate,
)
from .health import HealthResponse, HealthStatus
from .search import DictionaryEntryResponse, MeaningResponse, SearchRequest, SearchResponse

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
