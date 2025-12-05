"""FSRS service for spaced repetition scheduling."""

from datetime import UTC, datetime
from enum import IntEnum

from fsrs import FSRS, Card, Rating, ReviewLog


class CardState(IntEnum):
    """Card state enum matching FSRS."""

    New = 0
    Learning = 1
    Review = 2
    Relearning = 3


class FSRSService:
    """Service for FSRS spaced repetition scheduling."""

    def __init__(self):
        """Initialize FSRS scheduler with default parameters."""
        self.fsrs = FSRS()

    def create_card(self) -> Card:
        """Create a new FSRS card with default state."""
        return Card()

    def review_card(
        self, card: Card, rating: Rating, review_time: datetime | None = None
    ) -> tuple[Card, ReviewLog]:
        """
        Review a card and get updated state.

        Args:
            card: Current card state
            rating: User rating (Again=1, Hard=2, Good=3, Easy=4)
            review_time: Time of review (defaults to now)

        Returns:
            Tuple of (updated_card, review_log)
        """
        if review_time is None:
            review_time = datetime.now(UTC)

        scheduling_cards = self.fsrs.repeat(card, review_time)

        # Get the card for the selected rating
        updated_card = scheduling_cards[rating].card
        review_log = scheduling_cards[rating].review_log

        return updated_card, review_log

    def get_retrievability(self, card: Card, now: datetime | None = None) -> float:
        """
        Get current retrievability (probability of recall).

        Args:
            card: Card to check
            now: Current time (defaults to now)

        Returns:
            Retrievability as float between 0 and 1
        """
        if now is None:
            now = datetime.now(UTC)

        return self.fsrs.get_retrievability(card, now)

    def cards_from_flashcard(
        self,
        difficulty: float,
        stability: float,
        elapsed_days: int,
        scheduled_days: int,
        reps: int,
        lapses: int,
        state: int,
        last_review: datetime | None,
        due: datetime,
    ) -> Card:
        """
        Convert database flashcard fields to FSRS Card.

        Args:
            Database flashcard FSRS fields

        Returns:
            FSRS Card object
        """
        card = Card()
        card.difficulty = difficulty
        card.stability = stability
        card.elapsed_days = elapsed_days
        card.scheduled_days = scheduled_days
        card.reps = reps
        card.lapses = lapses
        card.state = state
        card.last_review = last_review
        card.due = due

        return card