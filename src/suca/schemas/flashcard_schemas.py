from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import timezone
from enum import Enum

# class DifficultyLevel(str, Enum):
#     EASY = "easy"
#     MEDIUM = "medium"
#     HARD = "hard"

# class StudyProgress(BaseModel):
#     last_studied: Optional[datetime] = None
#     times_studied: int = 0
#     times_correct: int = 0
#     difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
#     next_review: Optional[datetime] = None

class Flashcard(BaseModel):
    id: str = Field(alias="doc_id")
    user_id: str
    front: str
    back: str
    deck_id: Optional[str] = None
    updated_at: Optional[str] = None

class FlashcardCreate(BaseModel):
    deck_id: Optional[str] = None
    front: str
    back: str
    
class FlashcardUpdate(BaseModel):
    deck_id: Optional[str] = None
    front: Optional[str] = None
    back: Optional[str] = None

class FlashcardResponse(BaseModel):
    flashcards: List[Flashcard]
    total_count: int
    has_more: bool

class DeckCreate(BaseModel):
    name: str

# class StudySession(BaseModel):
#     flashcard_id: str
#     was_correct: bool
#     difficulty_rating: Optional[DifficultyLevel] = None
