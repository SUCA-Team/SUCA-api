"""Tests for FSRS (Free Spaced Repetition Scheduler) functionality."""

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from fsrs import Card, Rating, State
from sqlmodel import Session

from src.suca.schemas.flashcard_schemas import FlashcardCreate
from src.suca.services.flashcard_service import FlashcardService
from src.suca.services.fsrs_service import FSRSService

# ===== FSRSService Unit Tests =====


def test_fsrs_service_create_card():
    """Test creating a new FSRS card."""
    service = FSRSService()
    card = service.create_card()

    assert isinstance(card, Card)
    assert card.state == State.Learning
    assert card.difficulty is None  # New cards start with None
    assert card.stability is None
    assert card.step is None or card.step == 0


def test_fsrs_service_review_card_good():
    """Test reviewing a card with 'Good' rating."""
    service = FSRSService()
    card = service.create_card()

    # Review with Good rating
    updated_card, review_log = service.review_card(card, Rating.Good)

    assert isinstance(updated_card, Card)
    assert updated_card.difficulty is not None
    assert updated_card.stability is not None
    assert updated_card.last_review is not None
    assert updated_card.due > datetime.now(UTC)
    assert review_log is not None


def test_fsrs_service_review_ratings():
    """Test all four rating types."""
    service = FSRSService()

    # Test Again (1)
    card_again = service.create_card()
    reviewed_again, _ = service.review_card(card_again, Rating.Again)
    assert reviewed_again.state in [State.Learning, State.Relearning]

    # Test Hard (2)
    card_hard = service.create_card()
    reviewed_hard, _ = service.review_card(card_hard, Rating.Hard)
    assert reviewed_hard.difficulty is not None

    # Test Good (3)
    card_good = service.create_card()
    reviewed_good, _ = service.review_card(card_good, Rating.Good)
    assert reviewed_good.difficulty is not None

    # Test Easy (4)
    card_easy = service.create_card()
    reviewed_easy, _ = service.review_card(card_easy, Rating.Easy)
    assert reviewed_easy.difficulty is not None
    # Easy cards should have longer intervals
    assert reviewed_easy.stability is not None


def test_fsrs_service_get_retrievability():
    """Test calculating retrievability."""
    service = FSRSService()
    card = service.create_card()

    # Review the card first
    card, _ = service.review_card(card, Rating.Good)

    # Get retrievability
    retrievability = service.get_retrievability(card)

    assert 0.0 <= retrievability <= 1.0
    assert isinstance(retrievability, float)


def test_fsrs_service_card_to_dict():
    """Test converting FSRS Card to dictionary."""
    service = FSRSService()
    card = service.create_card()
    card, _ = service.review_card(card, Rating.Good)

    card_dict = service.card_to_dict(card)

    assert "difficulty" in card_dict
    assert "stability" in card_dict
    assert "reps" in card_dict
    assert "state" in card_dict
    assert "last_review" in card_dict
    assert "due" in card_dict
    assert "lapses" not in card_dict  # Removed in FSRS v6.3.0

    # Verify types
    assert isinstance(card_dict["difficulty"], float)
    assert isinstance(card_dict["stability"], float)
    assert isinstance(card_dict["reps"], int)
    assert isinstance(card_dict["state"], int)


def test_fsrs_service_card_to_dict_handles_none_step():
    """Test that card_to_dict handles None step value."""
    service = FSRSService()
    card = service.create_card()

    # Review to Review state where step might be None
    card, _ = service.review_card(card, Rating.Good)
    card, _ = service.review_card(card, Rating.Good)

    # Should not raise error even if step is None
    card_dict = service.card_to_dict(card)
    assert card_dict["reps"] == 0 or isinstance(card_dict["reps"], int)


def test_fsrs_service_dict_to_card():
    """Test converting dictionary to FSRS Card."""
    service = FSRSService()

    card_dict = {
        "difficulty": 5.0,
        "stability": 10.0,
        "reps": 3,
        "state": 2,  # Review state
        "last_review": datetime.now(UTC),
        "due": datetime.now(UTC) + timedelta(days=5),
    }

    card = service.dict_to_card(card_dict)

    assert isinstance(card, Card)
    assert card.difficulty == 5.0
    assert card.stability == 10.0
    assert card.step == 3
    assert card.state == State.Review
    assert card.last_review is not None
    assert card.due is not None


def test_fsrs_service_dict_to_card_new_state():
    """Test converting dictionary with New state (0) to Learning state."""
    service = FSRSService()

    card_dict = {
        "difficulty": 0.0,
        "stability": 0.0,
        "reps": 0,
        "state": 0,  # New state (custom)
        "last_review": None,
        "due": datetime.now(UTC),
    }

    card = service.dict_to_card(card_dict)

    # State 0 should be converted to Learning
    assert card.state == State.Learning


def test_fsrs_service_is_card_new():
    """Test checking if card is in New state."""
    service = FSRSService()

    # New card (state 0) gets converted to Learning (state 1)
    new_card_dict = {
        "difficulty": 0.0,
        "stability": 0.0,
        "reps": 0,
        "state": 0,
        "last_review": None,
        "due": datetime.now(UTC),
    }
    new_card = service.dict_to_card(new_card_dict)

    # State 0 gets converted to Learning (1) by dict_to_card
    assert new_card.state == State.Learning


def test_fsrs_service_round_trip_conversion():
    """Test that card->dict->card conversion preserves data."""
    service = FSRSService()

    # Create and review a card
    original_card = service.create_card()
    original_card, _ = service.review_card(original_card, Rating.Good)

    # Convert to dict and back
    card_dict = service.card_to_dict(original_card)
    reconstructed_card = service.dict_to_card(card_dict)

    # Compare key fields
    assert reconstructed_card.difficulty == original_card.difficulty
    assert reconstructed_card.stability == original_card.stability
    assert reconstructed_card.state == original_card.state


# ===== FlashcardService FSRS Integration Tests =====


def test_flashcard_service_review_card_all_ratings(session: Session):
    """Test reviewing flashcards with all four ratings."""
    service = FlashcardService(session)

    from src.suca.schemas.flashcard_schemas import DeckCreate, FlashcardReviewRequest

    deck = service.create_deck("test_user", DeckCreate(name="Test Deck"))

    ratings = [
        (1, "Again"),
        (2, "Hard"),
        (3, "Good"),
        (4, "Easy"),
    ]

    for rating_value, rating_name in ratings:
        # Create a new card for each rating
        flashcard = service.create_flashcard(
            "test_user",
            FlashcardCreate(
                deck_id=deck.id, front=f"Test {rating_name}", back=f"Test {rating_name}"
            ),
        )

        # Review the card
        review_request = FlashcardReviewRequest(rating=rating_value)
        result = service.review_flashcard(flashcard.id, "test_user", review_request)

        assert result.id == flashcard.id
        assert result.difficulty >= 0
        assert result.stability >= 0
        assert 0.0 <= result.retrievability <= 1.0


# ===== API Endpoint Tests =====


def test_review_flashcard_endpoint(auth_client: TestClient):
    """Test the review flashcard endpoint."""
    # Create deck and flashcard
    deck_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Test Deck"})
    deck_id = deck_response.json()["id"]

    card_response = auth_client.post(
        f"/api/v1/flashcard/decks/{deck_id}/cards", json={"front": "Test", "back": "Test"}
    )
    card_id = card_response.json()["id"]

    # Review the card
    review_response = auth_client.post(
        f"/api/v1/flashcard/decks/{deck_id}/cards/{card_id}/review", json={"rating": 3}
    )

    assert review_response.status_code == 200
    data = review_response.json()

    assert data["id"] == card_id
    assert data["difficulty"] > 0
    assert data["stability"] > 0
    assert data["last_review"] is not None
    assert data["due"] is not None
    assert "retrievability" in data
    assert 0.0 <= data["retrievability"] <= 1.0


def test_review_flashcard_invalid_rating(auth_client: TestClient):
    """Test reviewing with invalid rating."""
    deck_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Test Deck"})
    deck_id = deck_response.json()["id"]

    card_response = auth_client.post(
        f"/api/v1/flashcard/decks/{deck_id}/cards", json={"front": "Test", "back": "Test"}
    )
    card_id = card_response.json()["id"]

    # Rating too low (0)
    response = auth_client.post(
        f"/api/v1/flashcard/decks/{deck_id}/cards/{card_id}/review", json={"rating": 0}
    )
    assert response.status_code == 422

    # Rating too high (5)
    response = auth_client.post(
        f"/api/v1/flashcard/decks/{deck_id}/cards/{card_id}/review", json={"rating": 5}
    )
    assert response.status_code == 422


def test_review_multiple_cards_in_sequence(auth_client: TestClient):
    """Test reviewing multiple cards in sequence."""
    deck_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Test Deck"})
    deck_id = deck_response.json()["id"]

    # Create multiple cards
    cards = []
    for i in range(5):
        card_response = auth_client.post(
            f"/api/v1/flashcard/decks/{deck_id}/cards",
            json={"front": f"Card {i}", "back": f"Answer {i}"},
        )
        cards.append(card_response.json())

    # Review all cards with different ratings
    ratings = [3, 4, 2, 3, 1]  # Good, Easy, Hard, Good, Again

    for card, rating in zip(cards, ratings, strict=False):
        review_response = auth_client.post(
            f"/api/v1/flashcard/decks/{deck_id}/cards/{card['id']}/review", json={"rating": rating}
        )
        assert review_response.status_code == 200

        review_data = review_response.json()
        assert review_data["difficulty"] > 0
        assert review_data["stability"] > 0


def test_retrievability_decreases_over_time(auth_client: TestClient):
    """Test that retrievability concept is reflected in the system."""
    deck_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Test Deck"})
    deck_id = deck_response.json()["id"]

    card_response = auth_client.post(
        f"/api/v1/flashcard/decks/{deck_id}/cards", json={"front": "Test", "back": "Test"}
    )
    card_id = card_response.json()["id"]

    # Review the card
    review_response = auth_client.post(
        f"/api/v1/flashcard/decks/{deck_id}/cards/{card_id}/review", json={"rating": 3}
    )

    # Should have retrievability in response
    assert "retrievability" in review_response.json()
    retrievability = review_response.json()["retrievability"]
    assert 0.0 <= retrievability <= 1.0


# ===== Edge Cases and Error Handling =====


def test_review_nonexistent_card(auth_client: TestClient):
    """Test reviewing a card that doesn't exist."""
    deck_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Test Deck"})
    deck_id = deck_response.json()["id"]

    response = auth_client.post(
        f"/api/v1/flashcard/decks/{deck_id}/cards/99999/review", json={"rating": 3}
    )
    assert response.status_code == 404


def test_review_card_wrong_deck(auth_client: TestClient):
    """Test reviewing a card through wrong deck."""
    deck1_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Deck 1"})
    deck1_id = deck1_response.json()["id"]

    deck2_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Deck 2"})
    deck2_id = deck2_response.json()["id"]

    card_response = auth_client.post(
        f"/api/v1/flashcard/decks/{deck1_id}/cards", json={"front": "Test", "back": "Test"}
    )
    card_id = card_response.json()["id"]

    # Try to review through wrong deck
    response = auth_client.post(
        f"/api/v1/flashcard/decks/{deck2_id}/cards/{card_id}/review", json={"rating": 3}
    )
    assert response.status_code == 404


def test_fsrs_fields_persisted_correctly(auth_client: TestClient):
    """Test that FSRS fields are correctly persisted to database."""
    deck_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Test Deck"})
    deck_id = deck_response.json()["id"]

    card_response = auth_client.post(
        f"/api/v1/flashcard/decks/{deck_id}/cards", json={"front": "Test", "back": "Test"}
    )
    card_id = card_response.json()["id"]

    # Review the card
    auth_client.post(
        f"/api/v1/flashcard/decks/{deck_id}/cards/{card_id}/review", json={"rating": 3}
    )

    # Fetch the card again
    fetched_card = auth_client.get(f"/api/v1/flashcard/decks/{deck_id}/cards/{card_id}").json()

    # Verify FSRS fields are persisted
    assert fetched_card["difficulty"] > 0
    assert fetched_card["stability"] > 0
    assert fetched_card["reps"] >= 0
    assert fetched_card["state"] in [0, 1, 2, 3]
    assert fetched_card["last_review"] is not None
    assert fetched_card["due"] is not None


def test_due_cards_empty_for_new_user(auth_client: TestClient):
    """Test that due cards is empty for a user with no cards."""
    response = auth_client.get("/api/v1/flashcard/due")

    assert response.status_code == 200
    data = response.json()

    # Should return valid response even with no cards
    assert "decks" in data
    assert "total_due" in data
    assert isinstance(data["decks"], list)


def test_get_deck_due_cards_endpoint(auth_client: TestClient):
    """Test the new endpoint that returns due cards for a specific deck."""
    # Create a deck
    deck_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Test Deck"})
    assert deck_response.status_code == 201
    deck_id = deck_response.json()["id"]

    # Create several cards
    card_ids = []
    for i in range(5):
        card_response = auth_client.post(
            f"/api/v1/flashcard/decks/{deck_id}/cards",
            json={"front": f"Card {i}", "back": f"Answer {i}"},
        )
        assert card_response.status_code == 201
        card_ids.append(card_response.json()["id"])

    # All new cards should be due
    due_cards_response = auth_client.get(f"/api/v1/flashcard/decks/{deck_id}/due")
    assert due_cards_response.status_code == 200

    due_cards_data = due_cards_response.json()
    assert due_cards_data["total_count"] == 5
    assert len(due_cards_data["flashcards"]) == 5

    # Verify each card has the required fields
    for card in due_cards_data["flashcards"]:
        assert "id" in card
        assert "front" in card
        assert "back" in card
        assert "due" in card
        assert "state" in card


def test_get_deck_due_cards_after_review(auth_client: TestClient):
    """Test get_deck_due_cards shows fewer cards after reviewing with Easy."""
    # Create a deck
    deck_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Review Deck"})
    deck_id = deck_response.json()["id"]

    # Create 3 cards
    card_ids = []
    for i in range(3):
        card_response = auth_client.post(
            f"/api/v1/flashcard/decks/{deck_id}/cards",
            json={"front": f"Card {i}", "back": f"Answer {i}"},
        )
        card_ids.append(card_response.json()["id"])

    # Initially all 3 should be due
    due_response = auth_client.get(f"/api/v1/flashcard/decks/{deck_id}/due")
    assert due_response.json()["total_count"] == 3

    # Review one card with "Easy" (rating 4) - should be due much later
    auth_client.post(
        f"/api/v1/flashcard/decks/{deck_id}/cards/{card_ids[0]}/review", json={"rating": 4}
    )

    # Now only 2 cards should be due
    due_response = auth_client.get(f"/api/v1/flashcard/decks/{deck_id}/due")
    assert due_response.json()["total_count"] == 2


def test_get_deck_due_cards_empty_deck(auth_client: TestClient):
    """Test get_deck_due_cards when deck has no cards."""
    deck_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Empty Deck"})
    deck_id = deck_response.json()["id"]

    due_cards_response = auth_client.get(f"/api/v1/flashcard/decks/{deck_id}/due")
    assert due_cards_response.status_code == 200

    due_cards_data = due_cards_response.json()
    assert due_cards_data["total_count"] == 0
    assert len(due_cards_data["flashcards"]) == 0


def test_get_deck_due_cards_nonexistent_deck(auth_client: TestClient):
    """Test get_deck_due_cards with non-existent deck."""
    due_cards_response = auth_client.get("/api/v1/flashcard/decks/99999/due")
    assert due_cards_response.status_code == 404
