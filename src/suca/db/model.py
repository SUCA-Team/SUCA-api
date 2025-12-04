from datetime import UTC, datetime
from typing import ClassVar

from sqlmodel import Field, Relationship, SQLModel


# Database models for the SUCA dictionary
class Entry(SQLModel, table=True):
    ent_seq: int = Field(primary_key=True)
    is_common: bool = Field(index=True)  # Index for filtering common words
    jlpt_level: str | None = Field(default=None, index=True)  # Index for JLPT filtering

    kanjis: list["Kanji"] = Relationship(back_populates="entry")
    readings: list["Reading"] = Relationship(back_populates="entry")
    senses: list["Sense"] = Relationship(back_populates="entry")


class Kanji(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    keb: str = Field(index=True)  # Index for text search
    ke_inf: str | None = None
    ke_pri: str | None = None
    entry_id: int = Field(foreign_key="entry.ent_seq", index=True)
    entry: "Entry" = Relationship(back_populates="kanjis")


class Reading(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    reb: str = Field(index=True)  # Index for text search
    re_nokanji: str | None = None
    re_pri: str | None = None
    re_inf: str | None = None
    entry_id: int = Field(foreign_key="entry.ent_seq", index=True)
    entry: "Entry" = Relationship(back_populates="readings")


class Sense(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    entry_id: int = Field(foreign_key="entry.ent_seq", index=True)
    pos: str | None = None
    field: str | None = None
    misc: str | None = None

    entry: "Entry" = Relationship(back_populates="senses")
    glosses: list["Gloss"] = Relationship(back_populates="sense")
    examples: list["Example"] = Relationship(back_populates="sense")


class Gloss(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    sense_id: int = Field(foreign_key="sense.id", index=True)
    lang: str = Field(index=True)  # Index for language filtering
    text: str = Field(index=True)  # Index for text search
    sense: "Sense" = Relationship(back_populates="glosses")


class Example(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    sense_id: int = Field(foreign_key="sense.id", index=True)
    text: str
    sense: "Sense" = Relationship(back_populates="examples")


# Database models for the SUCA flashcard
class FlashcardDeck(SQLModel, table=True):
    """Flashcard deck model."""

    __tablename__: ClassVar[str] = "flashcard_decks"  # type: ignore[misc]

    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationships
    flashcards: list["Flashcard"] = Relationship(back_populates="deck")


class Flashcard(SQLModel, table=True):
    """Flashcard model."""

    __tablename__: ClassVar[str] = "flashcards"  # type: ignore[misc]

    id: int | None = Field(default=None, primary_key=True)
    deck_id: int = Field(foreign_key="flashcard_decks.id", index=True)
    user_id: str = Field(index=True)
    front: str
    back: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationships
    deck: FlashcardDeck | None = Relationship(back_populates="flashcards")
