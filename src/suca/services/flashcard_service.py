"""Flashcard service for business logic."""

from datetime import UTC, datetime

from fsrs import Rating
from sqlmodel import func, select

from ..core.exceptions import DatabaseException, ValidationException
from ..db.model import Flashcard, FlashcardDeck
from ..schemas.flashcard_schemas import (
    DeckCreate,
    DeckListResponse,
    DeckResponse,
    DeckUpdate,
    DueCardsResponse,
    DueDeckStats,
    FlashcardCreate,
    FlashcardListResponse,
    FlashcardResponse,
    FlashcardReviewRequest,
    FlashcardReviewResponse,
    FlashcardUpdate,
)
from .base import BaseService
from .fsrs_service import CardState, FSRSService


class FlashcardService(BaseService[Flashcard]):
    """Service for flashcard operations."""

    def __init__(self, session):
        """Initialize with session and FSRS service."""
        super().__init__(session)
        self.fsrs_service = FSRSService()

    def create_deck(self, user_id: str, deck_create: DeckCreate) -> DeckResponse:
        """Create a new flashcard deck."""
        try:
            deck = FlashcardDeck(
                user_id=user_id,
                name=deck_create.name,
                description=deck_create.description,
                is_public=deck_create.is_public if deck_create.is_public is not None else False,
            )
            self.session.add(deck)
            self.session.commit()
            self.session.refresh(deck)

            return DeckResponse(
                id=deck.id,
                user_id=deck.user_id,
                name=deck.name,
                description=deck.description,
                is_public=deck.is_public,
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
                    description=deck.description,
                    is_public=deck.is_public,
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
                description=deck.description,
                is_public=deck.is_public,
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
        if deck_update.description is not None:
            deck.description = deck_update.description
        if deck_update.is_public is not None:
            deck.is_public = deck_update.is_public

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
                description=deck.description,
                is_public=deck.is_public,
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
            # Create new FSRS card
            fsrs_card = self.fsrs_service.create_card()
            card_data = self.fsrs_service.card_to_dict(fsrs_card)

            flashcard = Flashcard(
                deck_id=flashcard_create.deck_id,
                user_id=user_id,
                front=flashcard_create.front,
                back=flashcard_create.back,
                # Initialize FSRS fields
                **card_data,
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

    def review_flashcard(
        self, card_id: int, user_id: str, review: FlashcardReviewRequest
    ) -> FlashcardReviewResponse:
        """
        Review a flashcard and update FSRS state.

        Args:
            card_id: Flashcard ID
            user_id: User ID
            review: Review with rating (1-4)

        Returns:
            Updated flashcard with new FSRS state
        """
        flashcard = self._get_flashcard_by_id(card_id, user_id)

        try:
            # Convert flashcard to FSRS card
            card_dict = {
                "difficulty": flashcard.difficulty,
                "stability": flashcard.stability,
                "reps": flashcard.reps,
                "state": flashcard.state,
                "last_review": flashcard.last_review,
                "due": flashcard.due,
            }
            fsrs_card = self.fsrs_service.dict_to_card(card_dict)

            # Review the card
            rating = Rating(review.rating)
            updated_card, _ = self.fsrs_service.review_card(fsrs_card, rating)

            # Update flashcard with new FSRS state
            updated_data = self.fsrs_service.card_to_dict(updated_card)
            flashcard.difficulty = updated_data["difficulty"]
            flashcard.stability = updated_data["stability"]
            flashcard.reps = updated_data["reps"]
            flashcard.state = updated_data["state"]
            flashcard.last_review = updated_data["last_review"]
            flashcard.due = updated_data["due"]
            flashcard.updated_at = datetime.now(UTC)

            self.session.add(flashcard)
            self.session.commit()
            self.session.refresh(flashcard)

            # Calculate current retrievability
            now = datetime.now(UTC)
            retrievability = self.fsrs_service.get_retrievability(updated_card, now)

            # Create response with all fields including retrievability
            response_data = flashcard.model_dump()
            response_data["retrievability"] = retrievability
            response = FlashcardReviewResponse.model_validate(response_data)

            return response

        except Exception as e:
            self.session.rollback()
            raise DatabaseException(f"Failed to review flashcard: {str(e)}")

    def get_due_cards(self, user_id: str) -> DueCardsResponse:
        """
        Get all cards due for review across all decks.

        Args:
            user_id: User ID

        Returns:
            Statistics for due cards in each deck
        """
        try:
            now = datetime.now(UTC)

            # Get all user's decks
            deck_statement = select(FlashcardDeck).where(FlashcardDeck.user_id == user_id)
            decks = self.session.exec(deck_statement).all()

            deck_stats = []
            total_due = 0

            for deck in decks:
                # Get all cards in deck
                card_statement = select(Flashcard).where(Flashcard.deck_id == deck.id)
                cards = self.session.exec(card_statement).all()

                total_cards = len(cards)
                new_cards = sum(1 for c in cards if c.state == CardState.New)
                learning_cards = sum(1 for c in cards if c.state == CardState.Learning)
                review_cards = sum(1 for c in cards if c.state == CardState.Review)
                # Database now stores timezone-aware datetimes
                due_cards = sum(1 for c in cards if c.due <= now)

                deck_stats.append(
                    DueDeckStats(
                        deck_id=deck.id,
                        deck_name=deck.name,
                        total_cards=total_cards,
                        new_cards=new_cards,
                        learning_cards=learning_cards,
                        review_cards=review_cards,
                        due_cards=due_cards,
                    )
                )

                total_due += due_cards

            return DueCardsResponse(
                decks=deck_stats,
                total_due=total_due,
            )

        except Exception as e:
            raise DatabaseException(f"Failed to get due cards: {str(e)}")

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

    def get_public_decks(self, limit: int = 50, offset: int = 0) -> DeckListResponse:
        """Get all public (shared) decks."""
        try:
            statement = (
                select(FlashcardDeck, func.count(Flashcard.id).label("flashcard_count"))
                .outerjoin(Flashcard, FlashcardDeck.id == Flashcard.deck_id)
                .where(FlashcardDeck.is_public)
                .group_by(FlashcardDeck.id)
                .order_by(FlashcardDeck.updated_at.desc())
                .limit(limit)
                .offset(offset)
            )

            results = self.session.exec(statement).all()

            decks = [
                DeckResponse(
                    id=deck.id,
                    user_id=deck.user_id,
                    name=deck.name,
                    description=deck.description,
                    is_public=deck.is_public,
                    created_at=deck.created_at,
                    updated_at=deck.updated_at,
                    flashcard_count=count,
                )
                for deck, count in results
            ]

            return DeckListResponse(decks=decks, total_count=len(decks))
        except Exception as e:
            raise DatabaseException(f"Failed to get public decks: {str(e)}")

    def get_public_deck(self, deck_id: int) -> DeckResponse:
        """Get a public deck by ID (no ownership check)."""
        try:
            statement = select(FlashcardDeck).where(
                FlashcardDeck.id == deck_id, FlashcardDeck.is_public
            )
            deck = self.session.exec(statement).first()

            if not deck:
                raise ValidationException(f"Public deck with id {deck_id} not found")

            count = self.session.exec(
                select(func.count(Flashcard.id)).where(Flashcard.deck_id == deck_id)
            ).one()

            return DeckResponse(
                id=deck.id,
                user_id=deck.user_id,
                name=deck.name,
                description=deck.description,
                is_public=deck.is_public,
                created_at=deck.created_at,
                updated_at=deck.updated_at,
                flashcard_count=count,
            )
        except ValidationException:
            raise
        except Exception as e:
            raise DatabaseException(f"Failed to get public deck: {str(e)}")

    def get_public_deck_flashcards(self, deck_id: int) -> FlashcardListResponse:
        """Get all flashcards from a public deck."""
        try:
            # Verify deck is public
            statement = select(FlashcardDeck).where(
                FlashcardDeck.id == deck_id, FlashcardDeck.is_public
            )
            deck = self.session.exec(statement).first()

            if not deck:
                raise ValidationException(f"Public deck with id {deck_id} not found")

            # Get flashcards
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
        except ValidationException:
            raise
        except Exception as e:
            raise DatabaseException(f"Failed to get public deck flashcards: {str(e)}")

    def copy_deck_to_user(
        self, source_deck_id: int, user_id: str, new_name: str | None = None
    ) -> DeckResponse:
        """Copy a public deck to user's collection."""
        try:
            # Get source deck (must be public)
            source_deck = self.get_public_deck(source_deck_id)

            # Get source flashcards
            source_flashcards = self.get_public_deck_flashcards(source_deck_id)

            # Create new deck for user
            deck_name = new_name if new_name else f"{source_deck.name} (Copy)"
            new_deck = FlashcardDeck(
                user_id=user_id,
                name=deck_name,
                description=source_deck.description,
                is_public=False,  # Copied decks are private by default
            )
            self.session.add(new_deck)
            self.session.flush()  # Get deck ID without committing

            # Copy flashcards
            for source_card in source_flashcards.flashcards:
                new_card = Flashcard(
                    deck_id=new_deck.id,
                    user_id=user_id,
                    front=source_card.front,
                    back=source_card.back,
                )
                self.session.add(new_card)

            self.session.commit()
            self.session.refresh(new_deck)

            return DeckResponse(
                id=new_deck.id,
                user_id=new_deck.user_id,
                name=new_deck.name,
                description=new_deck.description,
                is_public=new_deck.is_public,
                created_at=new_deck.created_at,
                updated_at=new_deck.updated_at,
                flashcard_count=len(source_flashcards.flashcards),
            )
        except ValidationException:
            raise
        except Exception as e:
            self.session.rollback()
            raise DatabaseException(f"Failed to copy deck: {str(e)}")
