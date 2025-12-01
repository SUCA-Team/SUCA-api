from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime, timezone
from .base import BaseTable

# Database models for the SUCA dictionary
class Entry(SQLModel, table=True):
    ent_seq: int = Field(primary_key=True)
    is_common: bool
    jlpt_level: Optional[str] = None

    kanjis: List["Kanji"] = Relationship(back_populates="entry")
    readings: List["Reading"] = Relationship(back_populates="entry")
    senses: List["Sense"] = Relationship(back_populates="entry")

class Kanji(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    keb: str
    ke_inf: Optional[str] = None
    ke_pri: Optional[str] = None
    entry_id: int = Field(foreign_key="entry.ent_seq")
    entry: "Entry" = Relationship(back_populates="kanjis")

class Reading(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    reb: str
    re_nokanji: Optional[str] = None
    re_pri: Optional[str] = None
    re_inf: Optional[str] = None
    entry_id: int = Field(foreign_key="entry.ent_seq")
    entry: "Entry" = Relationship(back_populates="readings")

class Sense(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    entry_id: int = Field(foreign_key="entry.ent_seq")
    pos: Optional[str] = None
    field: Optional[str] = None
    misc: Optional[str] = None

    entry: "Entry" = Relationship(back_populates="senses")
    glosses: List["Gloss"] = Relationship(back_populates="sense")
    examples: List["Example"] = Relationship(back_populates="sense")

class Gloss(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sense_id: int = Field(foreign_key="sense.id")
    lang: str
    text: str
    sense: "Sense" = Relationship(back_populates="glosses")

class Example(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sense_id: int = Field(foreign_key="sense.id")
    text: str
    sense: "Sense" = Relationship(back_populates="examples")

# Database models for the SUCA flashcard
class FlashcardDeck(SQLModel, table=True):
    """Flashcard deck model."""
    __tablename__ = "flashcard_decks"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    flashcards: List["Flashcard"] = Relationship(back_populates="deck")

class Flashcard(SQLModel, table=True):
    """Flashcard model."""
    __tablename__ = "flashcards"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    deck_id: int = Field(foreign_key="flashcard_decks.id", index=True)
    user_id: str = Field(index=True)
    front: str
    back: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    deck: Optional[FlashcardDeck] = Relationship(back_populates="flashcards")