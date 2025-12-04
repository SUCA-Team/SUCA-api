"""Search-related schemas."""

from typing import Any

from pydantic import BaseModel, Field

from .base import BaseResponse


class MeaningResponse(BaseModel):
    """Response model for word meanings."""

    pos: list[str] = Field(description="Parts of speech")
    definitions: list[str] = Field(description="English definitions")
    examples: list[dict[str, Any]] = Field(default=[], description="Usage examples")
    notes: list[str] = Field(default=[], description="Additional notes")


class DictionaryEntryResponse(BaseModel):
    """Response model for dictionary entries."""

    word: str = Field(description="Primary word form")
    reading: str | None = Field(None, description="Reading/pronunciation")
    is_common: bool = Field(False, description="Whether word is commonly used")
    jlpt_level: str | None = Field(None, description="JLPT level")
    meanings: list[MeaningResponse] = Field(description="Word meanings and definitions")
    other_forms: list[str] = Field(default=[], description="Alternative forms")
    tags: list[str] = Field(default=[], description="Word tags")
    variants: list[dict[str, str]] = Field(default=[], description="Kanji/reading variants")


class SearchResponse(BaseResponse):
    """Response model for search results."""

    results: list[DictionaryEntryResponse] = Field(description="Search results")
    total_count: int = Field(description="Total number of results found")
    query: str | None = Field(None, description="Original search query")


class SearchSuggestionResponse(BaseModel):
    """Response model for search suggestions."""

    suggestions: list[str] = Field(description="List of suggested words")


class SearchRequest(BaseModel):
    """Request model for search operations."""

    query: str = Field(min_length=1, description="Search query")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results to return")
    page: int = Field(default=1, ge=1, description="Page number for paginated results")
    include_rare: bool = Field(default=False, description="Include rare/uncommon words")
