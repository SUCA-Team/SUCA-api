"""Flashcard service with FSRS integration."""

from datetime import UTC, datetime

from sqlmodel import Session, col, select

from root_fsrs import FSRS, Card, Rating
from ..core.exceptions import DatabaseException, ValidationException
from ..db.model import Flashcard, FlashcardDeck
from ..schemas.flashcard_schemas import (
    DeckCreate,
    DeckUpdate,
    FlashcardCreate,
    FlashcardCreateNested,
    FlashcardListResponse,
    FlashcardResponse,
    FlashcardReviewRequest,
    FlashcardReviewResponse,
    FlashcardUpdate,
)
from .base import BaseService


class FlashcardService(BaseService[Flashcard]):
    """Service for flashcard operations with FSRS scheduling."""

    def __init__(self, session: Session):
        super().__init__(session)
        # Initialize FSRS scheduler
        self.scheduler = FSRS(
            request_retention=0.9,  # Target 90% retention
            maximum_interval=36500,  # Max ~100 years
            enable_fuzz=True,  # Add randomness to prevent clustering
        )

    # === Deck Operations ===

    def create_deck(self, deck_data: DeckCreate, user_id: str) -> FlashcardDeck:
        """Create a new flashcard deck."""
        try:
            deck = FlashcardDeck(
                user_id=user_id, name=deck_data.name, created_at=datetime.now(UTC)
            )

            self.session.add(deck)
            self.session.commit()
            self.session.refresh(deck)

            return deck

        except Exception as e:
            self.session.rollback()
            self._handle_db_error(e, "create deck")

    def get_decks(self, user_id: str) -> list[FlashcardDeck]:
        """Get all decks for a user."""
        try:
            statement = select(FlashcardDeck).where(FlashcardDeck.user_id == user_id)
            return list(self.session.exec(statement).all())

        except Exception as e:
            self._handle_db_error(e, "get decks")

    def get_deck_by_id(self, deck_id: int, user_id: str) -> FlashcardDeck:
        """Get a specific deck by ID."""
        return self._get_deck_by_id(deck_id, user_id)

    def update_deck(
        self, deck_id: int, deck_data: DeckUpdate, user_id: str
    ) -> FlashcardDeck:
        """Update a flashcard deck."""
        deck = self._get_deck_by_id(deck_id, user_id)

        try:
            if deck_data.name is not None:
                deck.name = deck_data.name

            deck.updated_at = datetime.now(UTC)

            self.session.add(deck)
            self.session.commit()
            self.session.refresh(deck)

            return deck

        except Exception as e:
            self.session.rollback()
            self._handle_db_error(e, "update deck")

    def delete_deck(self, deck_id: int, user_id: str) -> bool:
        """Delete a flashcard deck and all its cards."""
        deck = self._get_deck_by_id(deck_id, user_id)

        try:
            self.session.delete(deck)
            self.session.commit()
            return True

        except Exception as e:
            self.session.rollback()
            raise DatabaseException(f"Failed to delete deck: {str(e)}")

    # === Flashcard CRUD Operations ===

    def create_flashcard(
        self, deck_id: int, flashcard_data: FlashcardCreateNested, user_id: str
    ) -> Flashcard:
        """Create a new flashcard with FSRS initialization."""
        deck = self._get_deck_by_id(deck_id, user_id)

        try:
            flashcard = Flashcard(
                deck_id=deck.id,
                user_id=user_id,
                front=flashcard_data.front,
                back=flashcard_data.back,
                # FSRS default values for new card
                due=datetime.now(UTC),
                stability=0.0,
                difficulty=0.0,
                state=0,  # New card
                reps=0,
                lapses=0,
            )

            self.session.add(flashcard)
            self.session.commit()
            self.session.refresh(flashcard)

            return flashcard

        except Exception as e:
            self.session.rollback()
            self._handle_db_error(e, "create flashcard")

    def get_flashcards(
        self, deck_id: int, user_id: str, page: int = 1, page_size: int = 50
    ) -> FlashcardListResponse:
        """Get all flashcards in a deck with pagination."""
        self._get_deck_by_id(deck_id, user_id)

        try:
            # Count total
            count_stmt = select(Flashcard).where(
                Flashcard.deck_id == deck_id, Flashcard.user_id == user_id
            )
            total_count = len(list(self.session.exec(count_stmt).all()))

            # Get paginated results
            offset = (page - 1) * page_size
            statement = (
                select(Flashcard)
                .where(Flashcard.deck_id == deck_id, Flashcard.user_id == user_id)
                .offset(offset)
                .limit(page_size)
            )

            flashcards = list(self.session.exec(statement).all())

            return FlashcardListResponse(
                flashcards=[FlashcardResponse.model_validate(fc) for fc in flashcards],
                total_count=total_count,
                page=page,
                page_size=page_size,
            )

        except Exception as e:
            self._handle_db_error(e, "get flashcards")

    def get_flashcard_by_id(
        self, deck_id: int, card_id: int, user_id: str
    ) -> Flashcard:
        """Get a specific flashcard by ID."""
        return self._get_flashcard_by_id(card_id, user_id)

    def update_flashcard(
        self, deck_id: int, card_id: int, flashcard_data: FlashcardUpdate, user_id: str
    ) -> Flashcard:
        """Update a flashcard."""
        flashcard = self._get_flashcard_by_id(card_id, user_id)

        if flashcard.deck_id != deck_id:
            raise ValidationException("Flashcard does not belong to this deck")

        try:
            if flashcard_data.front is not None:
                flashcard.front = flashcard_data.front

            if flashcard_data.back is not None:
                flashcard.back = flashcard_data.back

            flashcard.updated_at = datetime.now(UTC)

            self.session.add(flashcard)
            self.session.commit()
            self.session.refresh(flashcard)

            return flashcard

        except Exception as e:
            self.session.rollback()
            self._handle_db_error(e, "update flashcard")

    def delete_flashcard(self, deck_id: int, card_id: int, user_id: str) -> bool:
        """Delete a flashcard."""
        flashcard = self._get_flashcard_by_id(card_id, user_id)

        if flashcard.deck_id != deck_id:
            raise ValidationException("Flashcard does not belong to this deck")

        try:
            self.session.delete(flashcard)
            self.session.commit()
            return True

        except Exception as e:
            self.session.rollback()
            raise DatabaseException(f"Failed to delete flashcard: {str(e)}")

    # === FSRS Review Operations ===

    def review_flashcard(
        self, deck_id: int, card_id: int, review_data: FlashcardReviewRequest, user_id: str
    ) -> FlashcardReviewResponse:
        """
        Process flashcard review using FSRS algorithm.

        Args:
            deck_id: ID of the deck
            card_id: ID of the flashcard
            review_data: Review request with rating (1=Again, 2=Hard, 3=Good, 4=Easy)
            user_id: ID of the user

        Returns:
            Review response with next schedule information
        """
        flashcard = self._get_flashcard_by_id(card_id, user_id)

        if flashcard.deck_id != deck_id:
            raise ValidationException("Flashcard does not belong to this deck")

        try:
            # Convert to FSRS Card
            fsrs_card = Card(
                due=flashcard.due,
                stability=flashcard.stability,
                difficulty=flashcard.difficulty,
                elapsed_days=flashcard.elapsed_days,
                scheduled_days=flashcard.scheduled_days,
                reps=flashcard.reps,
                lapses=flashcard.lapses,
                state=flashcard.state,
                last_review=flashcard.last_review,
            )

            # Get rating from request
            rating = Rating(review_data.rating)

            # Calculate next schedule using FSRS
            now = datetime.now(UTC)
            schedule_result = self.scheduler.repeat(fsrs_card, now)
            next_card, review_log = schedule_result[rating]

            # Update flashcard with new FSRS values
            flashcard.due = next_card.due
            flashcard.stability = next_card.stability
            flashcard.difficulty = next_card.difficulty
            flashcard.elapsed_days = next_card.elapsed_days
            flashcard.scheduled_days = next_card.scheduled_days
            flashcard.reps = next_card.reps
            flashcard.lapses = next_card.lapses
            flashcard.state = next_card.state
            flashcard.last_review = now
            flashcard.updated_at = now

            self.session.add(flashcard)
            self.session.commit()
            self.session.refresh(flashcard)

            return FlashcardReviewResponse(
                flashcard_id=flashcard.id,
                next_review=next_card.due,
                interval_days=next_card.scheduled_days,
                stability=next_card.stability,
                difficulty=next_card.difficulty,
                review_count=next_card.reps,
                lapse_count=next_card.lapses,
            )

        except Exception as e:
            self.session.rollback()
            self._handle_db_error(e, "review flashcard")

    def get_due_flashcards(
        self, user_id: str, deck_id: int | None = None, limit: int = 20
    ) -> list[Flashcard]:
        """Get flashcards that are due for review."""
        try:
            now = datetime.now(UTC)
            stmt = select(Flashcard).where(
                Flashcard.user_id == user_id, col(Flashcard.due) <= now
            )

            if deck_id:
                stmt = stmt.where(Flashcard.deck_id == deck_id)

            stmt = stmt.order_by(Flashcard.due).limit(limit)

            return list(self.session.exec(stmt).all())

        except Exception as e:
            self._handle_db_error(e, "get due flashcards")

    # === Helper Methods ===

    def _get_deck_by_id(self, deck_id: int, user_id: str) -> FlashcardDeck:
        """Get deck by ID and verify ownership."""
        statement = select(FlashcardDeck).where(
            FlashcardDeck.id == deck_id, FlashcardDeck.user_id == user_id
        )
        deck = self.session.exec(statement).first()

        if not deck:
            raise ValidationException(f"Deck with id {deck_id} not found")

        return deck

    def _get_flashcard_by_id(self, card_id: int, user_id: str) -> Flashcard:
        """Get flashcard by ID and verify ownership."""
        statement = select(Flashcard).where(
            Flashcard.id == card_id, Flashcard.user_id == user_id
        )
        flashcard = self.session.exec(statement).first()

        if not flashcard:
            raise ValidationException(f"Flashcard with id {card_id} not found")

        return flashcard