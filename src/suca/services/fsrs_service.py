"""FSRS service for spaced repetition algorithm."""

from datetime import UTC, datetime
from enum import IntEnum

from fsrs import Card, Rating, ReviewLog, Scheduler, State


class CardState(IntEnum):
    """Card states matching FSRS State enum."""

    New = 0  # Our custom state for new cards (not in FSRS lib)
    Learning = 1
    Review = 2
    Relearning = 3


class FSRSService:
    """Service wrapper for FSRS (Free Spaced Repetition Scheduler)."""

    def __init__(self):
        """Initialize FSRS scheduler with default parameters."""
        self.scheduler = Scheduler()

    def create_card(self) -> Card:
        """
        Create a new FSRS card with default values.

        Returns:
            A new Card object in the Learning state (FSRS default)
        """
        return Card()

    def review_card(self, card: Card, rating: Rating) -> tuple[Card, ReviewLog]:
        """
        Review a card and get the updated card state.

        Args:
            card: The FSRS Card object to review
            rating: Rating enum (Again=1, Hard=2, Good=3, Easy=4)

        Returns:
            Tuple of (updated_card, review_log)
        """
        now = datetime.now(UTC)
        return self.scheduler.review_card(card, rating, now)

    def get_retrievability(self, card: Card, now: datetime | None = None) -> float:
        """
        Calculate current retrievability (recall probability) for a card.

        Args:
            card: The FSRS Card object
            now: Current time (defaults to now)

        Returns:
            Retrievability value between 0 and 1
        """
        if now is None:
            now = datetime.now(UTC)
        return self.scheduler.get_card_retrievability(card, now)

    def card_to_dict(self, card: Card) -> dict:
        """
        Convert FSRS Card to dict for database storage.

        Note: FSRS v6.3.0 uses 'step' field which we map to 'reps' column.

        Args:
            card: FSRS Card object

        Returns:
            Dictionary with card fields (all datetimes are timezone-aware)
        """
        # Ensure last_review is timezone-aware if not None
        last_review = card.last_review
        if last_review is not None and last_review.tzinfo is None:
            last_review = last_review.replace(tzinfo=UTC)

        # Ensure due is timezone-aware
        due = card.due
        if due.tzinfo is None:
            due = due.replace(tzinfo=UTC)

        return {
            "difficulty": card.difficulty if card.difficulty is not None else 0.0,
            "stability": card.stability if card.stability is not None else 0.0,
            "reps": card.step if card.step is not None else 0,  # Map step to reps, default to 0
            "state": card.state.value,
            "last_review": last_review,
            "due": due,
        }

    def dict_to_card(self, data: dict) -> Card:
        """
        Convert dictionary to FSRS Card object.

        Note: FSRS v6.3.0 uses 'step' field which we map from 'reps' column.

        Args:
            data: Dictionary with card fields

        Returns:
            FSRS Card object
        """
        card = Card()
        card.difficulty = data.get("difficulty") if data.get("difficulty") != 0.0 else None
        card.stability = data.get("stability") if data.get("stability") != 0.0 else None
        card.step = data.get("reps", 0)  # Map reps to step

        # Convert state integer to State enum
        # Note: State 0 (New) doesn't exist in FSRS v6.3.0, default to Learning
        state_value = data.get("state", 1)
        if state_value == 0:
            state_value = 1  # Convert New to Learning
        card.state = State(state_value)

        # Ensure timezone-aware datetimes
        last_review = data.get("last_review")
        if last_review is not None and last_review.tzinfo is None:
            # Convert naive datetime to UTC-aware
            last_review = last_review.replace(tzinfo=UTC)
        card.last_review = last_review

        due = data.get("due", datetime.now(UTC))
        if due.tzinfo is None:
            # Convert naive datetime to UTC-aware
            due = due.replace(tzinfo=UTC)
        card.due = due

        return card

    def is_card_new(self, card: Card) -> bool:
        """
        Check if a card is in the New state.

        Note: In FSRS v6.3.0, there's no explicit "New" state. A card is new if:
        - It's in Learning state (step 0)
        - Has no stability/difficulty
        - Has never been reviewed

        Args:
            card: FSRS Card object

        Returns:
            True if card is new (never reviewed)
        """
        return (
            card.state == State.Learning
            and card.step == 0
            and card.last_review is None
            and card.stability is None
        )

    def is_card_due(self, card: Card, now: datetime | None = None) -> bool:
        """
        Check if a card is due for review.

        Args:
            card: FSRS Card object
            now: Current time (defaults to now)

        Returns:
            True if card is due
        """
        if now is None:
            now = datetime.now(UTC)
        return card.due <= now

    def get_next_states(self, card: Card) -> dict[Rating, Card]:
        """
        Get preview of card states for each possible rating.

        Args:
            card: FSRS Card object

        Returns:
            Dictionary mapping Rating to the resulting Card state
        """
        now = datetime.now(UTC)
        result = {}

        for rating in [Rating.Again, Rating.Hard, Rating.Good, Rating.Easy]:
            updated_card, _ = self.scheduler.review_card(card, rating, now)
            result[rating] = updated_card

        return result
