"""
FSRS (Free Spaced Repetition Scheduler) algorithm.
Data is stored in PostgreSQL, not JSON files.
"""

from datetime import datetime, timedelta
from enum import IntEnum
from typing import Optional


class Rating(IntEnum):
    """User rating for flashcard review."""
    AGAIN = 1  # Completely forgot
    HARD = 2   # Remembered with difficulty
    GOOD = 3   # Remembered correctly
    EASY = 4   # Remembered very easily


class Card:
    """
    FSRS Card - represents flashcard state.
    This is a temporary object for calculations.
    Actual data is stored in PostgreSQL Flashcard model.
    """

    def __init__(
        self,
        due: datetime = None,
        stability: float = 0.0,
        difficulty: float = 0.0,
        elapsed_days: int = 0,
        scheduled_days: int = 0,
        reps: int = 0,
        lapses: int = 0,
        state: int = 0,
        last_review: Optional[datetime] = None,
    ):
        self.due = due or datetime.now()
        self.stability = stability
        self.difficulty = difficulty
        self.elapsed_days = elapsed_days
        self.scheduled_days = scheduled_days
        self.reps = reps
        self.lapses = lapses
        self.state = state
        self.last_review = last_review


class ReviewLog:
    """Log entry for a single review session."""

    def __init__(
        self,
        rating: Rating,
        scheduled_days: int,
        elapsed_days: int,
        review_time: datetime,
        state: int,
    ):
        self.rating = rating
        self.scheduled_days = scheduled_days
        self.elapsed_days = elapsed_days
        self.review_time = review_time
        self.state = state


class FSRS:
    """
    FSRS algorithm for spaced repetition scheduling.
    
    NOTE: This class only performs calculations.
    All data persistence is handled by SQLModel -> PostgreSQL.
    No JSON files are used.
    """

    def __init__(
        self,
        w: tuple[float, ...] = (
            0.4, 0.6, 2.4, 5.8, 4.93, 0.94, 0.86, 0.01, 1.49, 0.14,
            0.94, 2.18, 0.05, 0.34, 1.26, 0.29, 2.61,
        ),
        request_retention: float = 0.9,
        maximum_interval: int = 36500,
        enable_fuzz: bool = True,
    ):
        self.w = w
        self.request_retention = request_retention
        self.maximum_interval = maximum_interval
        self.enable_fuzz = enable_fuzz

    def repeat(self, card: Card, now: datetime) -> dict[Rating, tuple[Card, ReviewLog]]:
        """
        Calculate next review schedule for all possible ratings.
        
        Returns dictionary of (updated_card, review_log) for each rating.
        The returned Card is used to update the database Flashcard model.
        """
        if card.state == 0:  # New card
            card.elapsed_days = 0
        else:
            card.elapsed_days = (now - card.last_review).days if card.last_review else 0

        card.last_review = now
        card.reps += 1

        result = {}

        for rating in Rating:
            next_card = self._next_card(card, rating, now)
            review_log = ReviewLog(
                rating=rating,
                scheduled_days=next_card.scheduled_days,
                elapsed_days=card.elapsed_days,
                review_time=now,
                state=next_card.state,
            )
            result[rating] = (next_card, review_log)

        return result

    def _next_card(self, card: Card, rating: Rating, now: datetime) -> Card:
        """Calculate next card state based on rating."""
        import copy
        next_card = copy.deepcopy(card)

        if rating == Rating.AGAIN:
            next_card.lapses += 1
            next_card.scheduled_days = 1
            next_card.stability = self._calculate_stability(card, rating)
            next_card.difficulty = min(10, card.difficulty + 1)

        elif rating == Rating.HARD:
            next_card.scheduled_days = max(1, int(card.scheduled_days * 1.2))
            next_card.stability = self._calculate_stability(card, rating)

        elif rating == Rating.GOOD:
            next_card.scheduled_days = self._next_interval(card)
            next_card.stability = self._calculate_stability(card, rating)

        elif rating == Rating.EASY:
            next_card.scheduled_days = int(self._next_interval(card) * 1.3)
            next_card.stability = self._calculate_stability(card, rating)
            next_card.difficulty = max(1, card.difficulty - 1)

        next_card.due = now + timedelta(days=next_card.scheduled_days)
        next_card.state = 2  # Review state

        return next_card

    def _calculate_stability(self, card: Card, rating: Rating) -> float:
        """Calculate memory stability."""
        if card.state == 0:  # New card
            initial_stability = {
                Rating.AGAIN: self.w[0],
                Rating.HARD: self.w[1],
                Rating.GOOD: self.w[2],
                Rating.EASY: self.w[3],
            }
            return initial_stability.get(rating, self.w[2])

        retrievability = pow(1 + card.elapsed_days / (9 * card.stability), -1)

        stability_factor = {
            Rating.AGAIN: self.w[4],
            Rating.HARD: self.w[5],
            Rating.GOOD: self.w[6],
            Rating.EASY: self.w[7],
        }

        return card.stability * (
            1 + stability_factor.get(rating, self.w[6]) * (11 - card.difficulty) * retrievability
        )

    def _next_interval(self, card: Card) -> int:
        """Calculate next review interval in days."""
        interval = card.stability * (pow(self.request_retention, 1 / 9) - 1)
        interval = min(interval, self.maximum_interval)
        interval = max(1, int(interval))

        if self.enable_fuzz and interval > 2:
            import random
            fuzz_range = max(1, int(interval * 0.05))
            interval += random.randint(-fuzz_range, fuzz_range)

        return max(1, interval)