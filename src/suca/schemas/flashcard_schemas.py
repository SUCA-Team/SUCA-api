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

    # No deck_id here - it comes from URL path
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

    model_config = ConfigDict(from_attributes=True)


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
