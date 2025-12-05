"""Database models using SQLModel."""

from datetime import UTC, datetime
from typing import ClassVar

from sqlmodel import Field, Relationship, SQLModel


class Entry(SQLModel, table=True):
    """Dictionary entry model."""

    __tablename__: ClassVar[str] = "entry"  # type: ignore[misc]

    ent_seq: int = Field(primary_key=True)
    is_common: bool = Field(default=False, index=True)
    jlpt_level: str | None = Field(default=None, index=True)

    kanjis: list["Kanji"] = Relationship(back_populates="entry")
    readings: list["Reading"] = Relationship(back_populates="entry")
    senses: list["Sense"] = Relationship(back_populates="entry")


class Kanji(SQLModel, table=True):
    """Kanji form model."""

    __tablename__: ClassVar[str] = "kanji"  # type: ignore[misc]

    id: int | None = Field(default=None, primary_key=True)
    keb: str = Field(index=True)
    ke_inf: str | None = None
    ke_pri: str | None = None
    entry_id: int = Field(foreign_key="entry.ent_seq", index=True)
    entry: "Entry" = Relationship(back_populates="kanjis")


class Reading(SQLModel, table=True):
    """Reading form model."""

    __tablename__: ClassVar[str] = "reading"  # type: ignore[misc]

    id: int | None = Field(default=None, primary_key=True)
    reb: str = Field(index=True)
    re_nokanji: bool | None = None
    re_pri: str | None = None
    re_inf: str | None = None
    entry_id: int = Field(foreign_key="entry.ent_seq", index=True)
    entry: "Entry" = Relationship(back_populates="readings")


class Sense(SQLModel, table=True):
    """Sense (meaning) model."""

    __tablename__: ClassVar[str] = "sense"  # type: ignore[misc]

    id: int | None = Field(default=None, primary_key=True)
    pos: str | None = None
    entry_id: int = Field(foreign_key="entry.ent_seq", index=True)
    entry: "Entry" = Relationship(back_populates="senses")
    glosses: list["Gloss"] = Relationship(back_populates="sense")
    examples: list["Example"] = Relationship(back_populates="sense")


class Gloss(SQLModel, table=True):
    """Gloss (definition) model."""

    __tablename__: ClassVar[str] = "gloss"  # type: ignore[misc]

    id: int | None = Field(default=None, primary_key=True)
    text: str = Field(index=True)
    lang: str = Field(default="eng", index=True)
    sense_id: int = Field(foreign_key="sense.id", index=True)
    sense: "Sense" = Relationship(back_populates="glosses")


class Example(SQLModel, table=True):
    """Example usage model."""

    __tablename__: ClassVar[str] = "example"  # type: ignore[misc]

    id: int | None = Field(default=None, primary_key=True)
    text: str
    sense_id: int = Field(foreign_key="sense.id", index=True)
    sense: "Sense" = Relationship(back_populates="examples")


class FlashcardDeck(SQLModel, table=True):
    """Flashcard deck model."""

    __tablename__: ClassVar[str] = "flashcard_decks"  # type: ignore[misc]

    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    flashcards: list["Flashcard"] = Relationship(back_populates="deck")


class Flashcard(SQLModel, table=True):
    """Flashcard model with FSRS fields."""

    __tablename__: ClassVar[str] = "flashcards"  # type: ignore[misc]

    id: int | None = Field(default=None, primary_key=True)
    deck_id: int = Field(foreign_key="flashcard_decks.id", index=True)
    user_id: str = Field(index=True)
    front: str
    back: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # FSRS fields
    difficulty: float = Field(default=0.0)
    stability: float = Field(default=0.0)
    elapsed_days: int = Field(default=0)
    scheduled_days: int = Field(default=0)
    reps: int = Field(default=0)
    lapses: int = Field(default=0)
    state: int = Field(default=0)  # 0=New, 1=Learning, 2=Review, 3=Relearning
    last_review: datetime | None = Field(default=None)
    due: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationships
    deck: FlashcardDeck | None = Relationship(back_populates="flashcards")