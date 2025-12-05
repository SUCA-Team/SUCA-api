"""Flashcard schemas for request/response validation."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FlashcardBase(BaseModel):
    """Base flashcard schema."""

    front: str = Field(..., min_length=1, max_length=1000)
    back: str = Field(..., min_length=1, max_length=1000)


class FlashcardCreate(FlashcardBase):
    """Schema for creating flashcard (standalone endpoint)."""

    deck_id: int


class FlashcardCreateNested(FlashcardBase):
    """Schema for creating flashcard (nested under deck endpoint)."""

    pass


class FlashcardUpdate(BaseModel):
    """Schema for updating flashcard."""

    front: str | None = Field(None, min_length=1, max_length=1000)
    back: str | None = Field(None, min_length=1, max_length=1000)


class FlashcardResponse(FlashcardBase):
    """Schema for flashcard response."""

    id: int
    deck_id: int
    user_id: str
    created_at: datetime
    updated_at: datetime

    # FSRS fields
    difficulty: float
    stability: float
    elapsed_days: int
    scheduled_days: int
    reps: int
    lapses: int
    state: int
    last_review: datetime | None
    due: datetime

    model_config = ConfigDict(from_attributes=True)


class FlashcardReviewRequest(BaseModel):
    """Schema for reviewing a flashcard."""

    rating: int = Field(..., ge=1, le=4, description="1=Again, 2=Hard, 3=Good, 4=Easy")


class FlashcardReviewResponse(FlashcardResponse):
    """Schema for flashcard review response with next review info."""

    retrievability: float = Field(..., description="Current recall probability (0-1)")


class DeckBase(BaseModel):
    """Base deck schema."""

    name: str = Field(..., min_length=1, max_length=200)


class DeckCreate(DeckBase):
    """Schema for creating deck."""

    pass


class DeckUpdate(BaseModel):
    """Schema for updating deck."""

    name: str | None = Field(None, min_length=1, max_length=200)


class DeckResponse(DeckBase):
    """Schema for deck response."""

    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime
    flashcard_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class FlashcardListResponse(BaseModel):
    """Schema for flashcard list response."""

    flashcards: list[FlashcardResponse]
    total_count: int


class DeckListResponse(BaseModel):
    """Schema for deck list response."""

    decks: list[DeckResponse]
    total_count: int


class DueDeckStats(BaseModel):
    """Statistics for due cards in a deck."""

    deck_id: int
    deck_name: str
    total_cards: int
    new_cards: int
    learning_cards: int
    review_cards: int
    due_cards: int


class DueCardsResponse(BaseModel):
    """Response for due cards across all decks."""

    decks: list[DueDeckStats]
    total_due: int