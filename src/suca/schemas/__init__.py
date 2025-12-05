"""Schemas for the SUCA API."""

from .base import BaseResponse, ErrorResponse, PaginatedResponse
from .flashcard_schemas import (
    DeckBase,
    DeckCreate,
    DeckListResponse,
    DeckResponse,
    DeckUpdate,
    DueCardsResponse,
    DueDeckStats,
    FlashcardBase,
    FlashcardCreate,
    FlashcardCreateNested,
    FlashcardListResponse,
    FlashcardResponse,
    FlashcardReviewRequest,
    FlashcardReviewResponse,
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
    "FlashcardReviewRequest",
    "FlashcardReviewResponse",
    "DeckBase",
    "DeckCreate",
    "DeckUpdate",
    "DeckResponse",
    "FlashcardListResponse",
    "DeckListResponse",
    "DueDeckStats",
    "DueCardsResponse",
]
