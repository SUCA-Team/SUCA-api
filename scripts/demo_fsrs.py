"""
Standalone FSRS Flashcard Demo Application

This script demonstrates the FSRS (Free Spaced Repetition Scheduler) algorithm
with a simple command-line flashcard application that supports multiple users.

This is a demo/testing utility and is separate from the main API application.
For the production implementation, see src/suca/services/fsrs_service.py
"""

from datetime import datetime, timezone
import json
from pathlib import Path

from fsrs import Card, Rating, Scheduler, State


# ==========================
# CARD WRAPPER CLASS
# ==========================
class FlashcardDemo:
    """Wrapper for FSRS Card with flashcard information."""

    def __init__(
        self,
        front: str,
        back: str,
        card_id: int | None = None,
        fsrs_card: Card | None = None,
    ):
        self.card_id: int = card_id or int(datetime.now(timezone.utc).timestamp() * 1000)
        self.front: str = front
        self.back: str = back
        self.fsrs_card: Card = fsrs_card or Card()

    def to_dict(self) -> dict:
        """Convert to dict for saving to file."""
        return {
            "card_id": self.card_id,
            "front": self.front,
            "back": self.back,
            "card_json": self.fsrs_card.to_json(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FlashcardDemo":
        """Create FlashcardDemo from dict."""
        fsrs_card: Card = Card.from_json(data["card_json"])
        return cls(
            front=data["front"],
            back=data["back"],
            card_id=data["card_id"],
            fsrs_card=fsrs_card,
        )


# ==========================
# STORAGE
# ==========================
DATA_FILE: Path = Path(__file__).parent / "flashcards_demo_data.json"


def load_database() -> dict:
    """Load entire database."""
    if not DATA_FILE.exists():
        return {"users": {}}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content: str = f.read().strip()
            if not content:
                return {"users": {}}
            return json.loads(content)
    except (json.JSONDecodeError, ValueError):
        print("Warning: Data file corrupted. Starting fresh.")
        return {"users": {}}


def save_database(db: dict) -> None:
    """Save entire database."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def load_user_cards(db: dict, username: str) -> list[FlashcardDemo]:
    """Load cards for a user."""
    if username not in db["users"]:
        return []

    cards_data: list = db["users"][username].get("cards", [])
    return [FlashcardDemo.from_dict(c) for c in cards_data]


def save_user_cards(db: dict, username: str, cards: list[FlashcardDemo]) -> None:
    """Save cards for a user."""
    if username not in db["users"]:
        db["users"][username] = {"cards": []}

    db["users"][username]["cards"] = [c.to_dict() for c in cards]
    save_database(db)


# ==========================
# USER MANAGEMENT
# ==========================
def select_user(db: dict) -> str | None:
    """Select or create user."""
    users: list[str] = list(db["users"].keys())

    if not users:
        print("\nNo users found.")
        username: str = input("Enter new username: ").strip()
        if not username:
            print("Username cannot be empty!")
            return None
        db["users"][username] = {"cards": []}
        save_database(db)
        print(f"Created user: {username}")
        return username

    print("\n" + "=" * 50)
    print("AVAILABLE USERS")
    print("=" * 50)
    for i, user in enumerate(users, 1):
        card_count: int = len(db["users"][user].get("cards", []))
        print(f"{i}. {user} ({card_count} cards)")

    print("\n0. Create new user")
    print("=" * 50)

    choice: str = input("\nChoose user (number or name): ").strip()

    # Create new user
    if choice == "0":
        username: str = input("Enter new username: ").strip()
        if not username:
            print("Username cannot be empty!")
            return None
        if username in users:
            print("Username already exists!")
            return None
        db["users"][username] = {"cards": []}
        save_database(db)
        print(f"Created user: {username}")
        return username

    # Select by number
    if choice.isdigit() and 1 <= int(choice) <= len(users):
        return users[int(choice) - 1]

    # Select by name
    if choice in users:
        return choice

    print("Invalid choice!")
    return None


# ==========================
# HELPER FUNCTIONS
# ==========================
def is_card_new(card: Card) -> bool:
    """Check if card is new."""
    return card.state == State.New


def get_due_cards(cards: list[FlashcardDemo]) -> list[FlashcardDemo]:
    """Get list of due cards."""
    now: datetime = datetime.now(timezone.utc)

    learning: list[FlashcardDemo] = []
    review: list[FlashcardDemo] = []
    new: list[FlashcardDemo] = []

    for demo_card in cards:
        fsrs_card: Card = demo_card.fsrs_card

        # New card
        if is_card_new(fsrs_card):
            new.append(demo_card)
            continue

        # Card in learning/relearning state
        if fsrs_card.state in (State.Learning, State.Relearning):
            if fsrs_card.due <= now:
                learning.append(demo_card)

        # Card in review state
        elif fsrs_card.state == State.Review:
            if fsrs_card.due <= now:
                review.append(demo_card)

    # Priority: Learning > Review > New
    return learning + review + new


# ==========================
# ADD CARD
# ==========================
def add_card(db: dict, username: str, cards: list[FlashcardDemo]) -> None:
    """Add new card."""
    print("\n" + "=" * 50)
    print("ADD NEW CARD")
    print("=" * 50)

    front: str = input("Front (question/word): ").strip()
    if not front:
        print("Front cannot be empty!")
        return

    back: str = input("Back (answer/meaning): ").strip()
    if not back:
        print("Back cannot be empty!")
        return

    new_card: FlashcardDemo = FlashcardDemo(front, back)
    cards.append(new_card)
    save_user_cards(db, username, cards)

    print(f"Added card: {front} → {back}")


# ==========================
# REVIEW SESSION
# ==========================
def review_cards(
    db: dict, username: str, cards: list[FlashcardDemo], scheduler: Scheduler
) -> None:
    """Review session."""
    due_cards: list[FlashcardDemo] = get_due_cards(cards)

    if not due_cards:
        print("\nNo cards due now!")

        # Show next due time
        active_cards: list[FlashcardDemo] = [c for c in cards if not is_card_new(c.fsrs_card)]
        if active_cards:
            next_card: FlashcardDemo = min(active_cards, key=lambda c: c.fsrs_card.due)
            wait_time: float = (
                next_card.fsrs_card.due - datetime.now(timezone.utc)
            ).total_seconds()
            print(f"Next card due in {int(wait_time)} seconds")

        return

    print(f"\n{len(due_cards)} cards due for review")
    reviewed: int = 0

    for demo_card in due_cards:
        print("\n" + "=" * 50)
        print(f"Question: {demo_card.front}")
        print(f"State: {demo_card.fsrs_card.state.name}")

        input("\nPress Enter to show answer...")

        print(f"Answer: {demo_card.back}")
        print("\n" + "=" * 50)
        print("Rate this card:")
        print("  1 = Again (Forgot)")
        print("  2 = Hard  (Difficult)")
        print("  3 = Good  (OK)")
        print("  4 = Easy  (Too easy)")
        print("  q = Quit review")

        choice: str = input("\nYour choice: ").strip().lower()

        if choice == "q":
            save_user_cards(db, username, cards)
            print(f"\nReviewed {reviewed} cards. Progress saved!")
            return

        if choice not in ("1", "2", "3", "4"):
            print("Invalid choice, skipping...")
            continue

        rating_map: dict[str, Rating] = {
            "1": Rating.Again,
            "2": Rating.Hard,
            "3": Rating.Good,
            "4": Rating.Easy,
        }
        rating: Rating = rating_map[choice]

        # Review with FSRS
        now = datetime.now(timezone.utc)
        updated_card: Card
        updated_card, _log = scheduler.review_card(demo_card.fsrs_card, rating, now)
        demo_card.fsrs_card = updated_card

        save_user_cards(db, username, cards)
        reviewed += 1

        print(f"\nReviewed! Next due: {updated_card.due.strftime('%Y-%m-%d %H:%M')}")
        print(
            f"  Stability: {updated_card.stability:.2f} | "
            f"Difficulty: {updated_card.difficulty:.2f}"
        )

    print(f"\nSession complete! Reviewed {reviewed} cards.")


# ==========================
# STATISTICS
# ==========================
def show_stats(cards: list[FlashcardDemo]) -> None:
    """Show statistics."""
    if not cards:
        print("\nNo cards yet!")
        return

    new: int = sum(1 for c in cards if is_card_new(c.fsrs_card))
    learning: int = sum(
        1 for c in cards if c.fsrs_card.state in (State.Learning, State.Relearning)
    )
    review: int = sum(1 for c in cards if c.fsrs_card.state == State.Review)

    now: datetime = datetime.now(timezone.utc)
    due_count: int = sum(1 for c in cards if not is_card_new(c.fsrs_card) and c.fsrs_card.due <= now)

    print("\n" + "=" * 50)
    print("STATISTICS")
    print("=" * 50)
    print(f"Total cards: {len(cards)}")
    print(f"\nBy state:")
    print(f"  New: {new}")
    print(f"  Learning: {learning}")
    print(f"  Review: {review}")
    print(f"\nDue now: {due_count}")
    print("=" * 50)


# ==========================
# LIST CARDS
# ==========================
def list_cards(cards: list[FlashcardDemo]) -> None:
    """List all cards."""
    if not cards:
        print("\nNo cards yet!")
        return

    print("\n" + "=" * 50)
    print(f"ALL CARDS ({len(cards)})")
    print("=" * 50)

    for i, demo_card in enumerate(cards, 1):
        state: str = (
            demo_card.fsrs_card.state.name if not is_card_new(demo_card.fsrs_card) else "New"
        )
        print(f"{i}. {demo_card.front} → {demo_card.back} [{state}]")

    print("=" * 50)


# ==========================
# DELETE USER
# ==========================
def delete_user(db: dict) -> None:
    """Delete user."""
    users: list[str] = list(db["users"].keys())

    if not users:
        print("\nNo users to delete!")
        return

    print("\n" + "=" * 50)
    print("DELETE USER")
    print("=" * 50)
    for i, user in enumerate(users, 1):
        print(f"{i}. {user}")

    choice: str = input("\nEnter user number to delete (or 'cancel'): ").strip()

    if choice.lower() == "cancel":
        return

    if choice.isdigit() and 1 <= int(choice) <= len(users):
        username: str = users[int(choice) - 1]
        confirm: str = input(
            f"Delete user '{username}' and all cards? (yes/no): "
        ).strip().lower()

        if confirm == "yes":
            del db["users"][username]
            save_database(db)
            print(f"Deleted user: {username}")
        else:
            print("Deletion cancelled")
    else:
        print("Invalid choice!")


# ==========================
# MAIN
# ==========================
def main() -> None:
    """Main entry point for the flashcard demo."""
    print("=" * 50)
    print("FLASHCARD DEMO APP (FSRS) - MULTI-USER")
    print("=" * 50)

    db: dict = load_database()
    scheduler: Scheduler = Scheduler()

    # Select user
    username: str | None = select_user(db)
    if not username:
        return

    cards: list[FlashcardDemo] = load_user_cards(db, username)
    print(f"\nLogged in as: {username}")
    print(f"Loaded {len(cards)} cards")

    # Menu loop
    while True:
        print(f"\nUser: {username}")
        print("\n1) Review cards")
        print("2) Add new card")
        print("3) List all cards")
        print("4) Show statistics")
        print("5) Switch user")
        print("6) Delete user")
        print("7) Quit")

        choice: str = input("\nChoose: ").strip()

        if choice == "1":
            review_cards(db, username, cards, scheduler)

        elif choice == "2":
            add_card(db, username, cards)

        elif choice == "3":
            list_cards(cards)

        elif choice == "4":
            show_stats(cards)

        elif choice == "5":
            save_user_cards(db, username, cards)
            username = select_user(db)
            if not username:
                break
            cards = load_user_cards(db, username)
            print(f"\nSwitched to user: {username}")

        elif choice == "6":
            delete_user(db)
            # If current user was deleted, select another user
            if username not in db["users"]:
                username = select_user(db)
                if not username:
                    break
                cards = load_user_cards(db, username)

        elif choice in ("7", "q"):
            save_user_cards(db, username, cards)
            print("\nGoodbye!")
            break

        else:
            print("Invalid choice!")


if __name__ == "__main__":
    main()
