from datetime import UTC, datetime

from sqlmodel import Field, Relationship, SQLModel


class Entry(SQLModel, table=True):
    ent_seq: int = Field(primary_key=True)
    is_common: bool
    jlpt_level: str | None = None

    kanjis: list["Kanji"] = Relationship(back_populates="entry")
    readings: list["Reading"] = Relationship(back_populates="entry")
    senses: list["Sense"] = Relationship(back_populates="entry")


class Kanji(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    keb: str
    ke_inf: str | None = None
    ke_pri: str | None = None
    entry_id: int = Field(foreign_key="entry.ent_seq")
    entry: "Entry" = Relationship(back_populates="kanjis")


class Reading(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    reb: str
    re_nokanji: str | None = None
    re_pri: str | None = None
    re_inf: str | None = None
    entry_id: int = Field(foreign_key="entry.ent_seq")
    entry: "Entry" = Relationship(back_populates="readings")


class Sense(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    entry_id: int = Field(foreign_key="entry.ent_seq")
    pos: str | None = None
    field: str | None = None
    misc: str | None = None

    entry: "Entry" = Relationship(back_populates="senses")
    glosses: list["Gloss"] = Relationship(back_populates="sense")
    examples: list["Example"] = Relationship(back_populates="sense")


class Gloss(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    sense_id: int = Field(foreign_key="sense.id")
    lang: str
    text: str
    sense: "Sense" = Relationship(back_populates="glosses")


class Example(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    sense_id: int = Field(foreign_key="sense.id")
    text: str
    sense: "Sense" = Relationship(back_populates="examples")


# === Flashcard Models ===


class FlashcardDeck(SQLModel, table=True):
    """Flashcard deck model."""

    __tablename__ = "flashcard_decks"

    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationships
    flashcards: list["Flashcard"] = Relationship(
        back_populates="deck", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class Flashcard(SQLModel, table=True):
    """Flashcard model with FSRS scheduling - ALL DATA STORED IN DATABASE."""

    __tablename__ = "flashcards"

    # Basic fields
    id: int | None = Field(default=None, primary_key=True)
    deck_id: int = Field(foreign_key="flashcard_decks.id", index=True)
    user_id: str = Field(index=True)
    front: str
    back: str

    # ========== FSRS FIELDS (STORED IN POSTGRESQL) ==========
    due: datetime = Field(default_factory=lambda: datetime.now(UTC))
    stability: float = Field(default=0.0)
    difficulty: float = Field(default=0.0)
    elapsed_days: int = Field(default=0)
    scheduled_days: int = Field(default=0)
    reps: int = Field(default=0)
    lapses: int = Field(default=0)
    state: int = Field(default=0)  # 0=New, 1=Learning, 2=Review, 3=Relearning
    last_review: datetime | None = Field(default=None)
    # ========================================================

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationships
    deck: FlashcardDeck | None = Relationship(back_populates="flashcards")