"""Flashcard-related schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


# === Base Schemas ===


class FlashcardBase(BaseModel):
    """Base flashcard schema."""

    front: str = Field(..., min_length=1, description="Front of the flashcard")
    back: str = Field(..., min_length=1, description="Back of the flashcard")


class FlashcardCreate(FlashcardBase):
    """Schema for creating a flashcard (with deck_id)."""

    deck_id: int = Field(..., description="ID of the deck")


class FlashcardCreateNested(FlashcardBase):
    """Schema for creating a flashcard in nested route (no deck_id needed)."""

    pass


class FlashcardUpdate(BaseModel):
    """Schema for updating a flashcard."""

    front: str | None = Field(None, min_length=1, description="Front of the flashcard")
    back: str | None = Field(None, min_length=1, description="Back of the flashcard")


class FlashcardResponse(FlashcardBase):
    """Schema for flashcard response."""

    id: int
    deck_id: int
    user_id: str
    due: datetime
    stability: float
    difficulty: float
    reps: int
    lapses: int
    state: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FlashcardListResponse(BaseModel):
    """Schema for paginated flashcard list."""

    flashcards: list[FlashcardResponse]
    total_count: int
    page: int
    page_size: int


# === Review Schemas ===


class FlashcardReviewRequest(BaseModel):
    """Request schema for reviewing a flashcard."""

    rating: int = Field(
        ..., ge=1, le=4, description="Review rating: 1=Again, 2=Hard, 3=Good, 4=Easy"
    )

    model_config = {
        "json_schema_extra": {"examples": [{"rating": 3}]}  # Good
    }


class FlashcardReviewResponse(BaseModel):
    """Response schema for flashcard review."""

    flashcard_id: int
    next_review: datetime = Field(description="Next review date")
    interval_days: int = Field(description="Interval until next review in days")
    stability: float = Field(description="Memory stability")
    difficulty: float = Field(description="Card difficulty")
    review_count: int = Field(description="Total number of reviews")
    lapse_count: int = Field(description="Number of times forgotten")


class DueFlashcardsRequest(BaseModel):
    """Request schema for getting due flashcards."""

    deck_id: int | None = Field(None, description="Optional deck ID filter")
    limit: int = Field(20, ge=1, le=100, description="Maximum number of cards to return")


# === Deck Schemas ===


class DeckBase(BaseModel):
    """Base deck schema."""

    name: str = Field(..., min_length=1, max_length=100, description="Name of the deck")


class DeckCreate(DeckBase):
    """Schema for creating a deck."""

    pass


class DeckUpdate(BaseModel):
    """Schema for updating a deck."""

    name: str | None = Field(
        None, min_length=1, max_length=100, description="New name for the deck"
    )


class DeckResponse(DeckBase):
    """Schema for deck response."""

    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DeckListResponse(BaseModel):
    """Schema for deck list response."""

    decks: list[DeckResponse]
    total_count: int