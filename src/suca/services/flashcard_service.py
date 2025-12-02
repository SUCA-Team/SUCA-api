"""Flashcard service for business logic."""

from datetime import UTC, datetime

from sqlmodel import func, select

from ..core.exceptions import DatabaseException, ValidationException
from ..db.model import Flashcard, FlashcardDeck
from ..schemas.flashcard_schemas import (
    DeckCreate,
    DeckListResponse,
    DeckResponse,
    DeckUpdate,
    FlashcardCreate,
    FlashcardListResponse,
    FlashcardResponse,
    FlashcardUpdate,
)
from .base import BaseService


class FlashcardService(BaseService[Flashcard]):
    """Service for flashcard operations."""

    def create_deck(self, user_id: str, deck_create: DeckCreate) -> DeckResponse:
        """Create a new flashcard deck."""
        try:
            deck = FlashcardDeck(
                user_id=user_id,
                name=deck_create.name,
            )
            self.session.add(deck)
            self.session.commit()
            self.session.refresh(deck)

            return DeckResponse(
                id=deck.id,
                user_id=deck.user_id,
                name=deck.name,
                created_at=deck.created_at,
                updated_at=deck.updated_at,
                flashcard_count=0,
            )
        except Exception as e:
            self.session.rollback()
            raise DatabaseException(f"Failed to create deck: {str(e)}")

    def get_user_decks(self, user_id: str) -> DeckListResponse:
        """Get all decks for a user."""
        try:
            statement = (
                select(FlashcardDeck, func.count(Flashcard.id).label("flashcard_count"))
                .outerjoin(Flashcard, FlashcardDeck.id == Flashcard.deck_id)
                .where(FlashcardDeck.user_id == user_id)
                .group_by(FlashcardDeck.id)
                .order_by(FlashcardDeck.updated_at.desc())
            )

            results = self.session.exec(statement).all()

            decks = [
                DeckResponse(
                    id=deck.id,
                    user_id=deck.user_id,
                    name=deck.name,
                    created_at=deck.created_at,
                    updated_at=deck.updated_at,
                    flashcard_count=count,
                )
                for deck, count in results
            ]

            return DeckListResponse(decks=decks, total_count=len(decks))
        except Exception as e:
            raise DatabaseException(f"Failed to get decks: {str(e)}")

    def get_deck(self, deck_id: int, user_id: str) -> DeckResponse:
        """Get a specific deck."""
        deck = self._get_deck_by_id(deck_id, user_id)

        try:
            count = self.session.exec(
                select(func.count(Flashcard.id)).where(Flashcard.deck_id == deck_id)
            ).one()

            return DeckResponse(
                id=deck.id,
                user_id=deck.user_id,
                name=deck.name,
                created_at=deck.created_at,
                updated_at=deck.updated_at,
                flashcard_count=count,
            )
        except Exception as e:
            raise DatabaseException(f"Failed to get deck: {str(e)}")

    def update_deck(self, deck_id: int, user_id: str, deck_update: DeckUpdate) -> DeckResponse:
        """Update a deck."""
        deck = self._get_deck_by_id(deck_id, user_id)

        if deck_update.name is not None:
            deck.name = deck_update.name

        deck.updated_at = datetime.now(UTC)

        try:
            self.session.add(deck)
            self.session.commit()
            self.session.refresh(deck)

            count = self.session.exec(
                select(func.count(Flashcard.id)).where(Flashcard.deck_id == deck_id)
            ).one()

            return DeckResponse(
                id=deck.id,
                user_id=deck.user_id,
                name=deck.name,
                created_at=deck.created_at,
                updated_at=deck.updated_at,
                flashcard_count=count,
            )
        except Exception as e:
            self.session.rollback()
            raise DatabaseException(f"Failed to update deck: {str(e)}")

    def delete_deck(self, deck_id: int, user_id: str) -> bool:
        """Delete a deck and all its flashcards."""
        deck = self._get_deck_by_id(deck_id, user_id)

        try:
            statement = select(Flashcard).where(Flashcard.deck_id == deck_id)
            flashcards = self.session.exec(statement).all()
            for flashcard in flashcards:
                self.session.delete(flashcard)

            self.session.delete(deck)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise DatabaseException(f"Failed to delete deck: {str(e)}")

    def create_flashcard(
        self, user_id: str, flashcard_create: FlashcardCreate
    ) -> FlashcardResponse:
        """Create a new flashcard."""
        self._get_deck_by_id(flashcard_create.deck_id, user_id)

        try:
            flashcard = Flashcard(
                deck_id=flashcard_create.deck_id,
                user_id=user_id,
                front=flashcard_create.front,
                back=flashcard_create.back,
            )
            self.session.add(flashcard)
            self.session.commit()
            self.session.refresh(flashcard)

            deck = self.session.get(FlashcardDeck, flashcard_create.deck_id)
            deck.updated_at = datetime.now(UTC)
            self.session.add(deck)
            self.session.commit()

            return FlashcardResponse.model_validate(flashcard)
        except Exception as e:
            self.session.rollback()
            raise DatabaseException(f"Failed to create flashcard: {str(e)}")

    def get_deck_flashcards(self, deck_id: int, user_id: str) -> FlashcardListResponse:
        """Get all flashcards in a deck."""
        self._get_deck_by_id(deck_id, user_id)

        try:
            statement = (
                select(Flashcard)
                .where(Flashcard.deck_id == deck_id)
                .order_by(Flashcard.created_at.desc())
            )

            flashcards = self.session.exec(statement).all()

            return FlashcardListResponse(
                flashcards=[FlashcardResponse.model_validate(fc) for fc in flashcards],
                total_count=len(flashcards),
            )
        except Exception as e:
            raise DatabaseException(f"Failed to get flashcards: {str(e)}")

    def get_flashcard(self, card_id: int, user_id: str) -> FlashcardResponse:
        """Get a specific flashcard."""
        flashcard = self._get_flashcard_by_id(card_id, user_id)
        return FlashcardResponse.model_validate(flashcard)

    def update_flashcard(
        self, card_id: int, user_id: str, flashcard_update: FlashcardUpdate
    ) -> FlashcardResponse:
        """Update a flashcard."""
        flashcard = self._get_flashcard_by_id(card_id, user_id)

        if flashcard_update.front is not None:
            flashcard.front = flashcard_update.front
        if flashcard_update.back is not None:
            flashcard.back = flashcard_update.back

        flashcard.updated_at = datetime.now(UTC)

        try:
            self.session.add(flashcard)
            self.session.commit()
            self.session.refresh(flashcard)

            return FlashcardResponse.model_validate(flashcard)
        except Exception as e:
            self.session.rollback()
            raise DatabaseException(f"Failed to update flashcard: {str(e)}")

    def delete_flashcard(self, card_id: int, user_id: str) -> bool:
        """Delete a flashcard."""
        flashcard = self._get_flashcard_by_id(card_id, user_id)

        try:
            self.session.delete(flashcard)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise DatabaseException(f"Failed to delete flashcard: {str(e)}")

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
        statement = select(Flashcard).where(Flashcard.id == card_id, Flashcard.user_id == user_id)
        flashcard = self.session.exec(statement).first()

        if not flashcard:
            raise ValidationException(f"Flashcard with id {card_id} not found")

        return flashcard
