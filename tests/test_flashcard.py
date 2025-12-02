"""Tests for flashcard functionality."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from src.suca.core.exceptions import ValidationException
from src.suca.schemas.flashcard_schemas import (
    DeckCreate,
    FlashcardCreate,
)
from src.suca.services.flashcard_service import FlashcardService

# ===== Deck Tests =====


def test_create_deck(auth_client: TestClient):  # ← Changed
    """Test creating a new deck."""
    response = auth_client.post(  # ← Changed
        "/api/v1/flashcard/decks", json={"name": "My Test Deck"}
    )

    assert response.status_code == 201
    data = response.json()

    assert "id" in data
    assert data["name"] == "My Test Deck"
    assert data["user_id"] == "demo_user"
    assert data["flashcard_count"] == 0


def test_list_decks(auth_client: TestClient):  # ← Changed
    """Test listing all decks."""
    # Create decks
    auth_client.post("/api/v1/flashcard/decks", json={"name": "Deck 1"})
    auth_client.post("/api/v1/flashcard/decks", json={"name": "Deck 2"})

    # List decks
    response = auth_client.get("/api/v1/flashcard/decks")

    assert response.status_code == 200
    data = response.json()

    assert "decks" in data
    assert "total_count" in data
    assert data["total_count"] >= 2
    assert len(data["decks"]) >= 2


def test_get_deck(auth_client: TestClient):  # ← Changed
    """Test getting a specific deck."""
    # Create a deck
    create_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Test Deck"})
    deck_id = create_response.json()["id"]

    # Get the deck
    response = auth_client.get(f"/api/v1/flashcard/decks/{deck_id}")

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == deck_id
    assert data["name"] == "Test Deck"
    assert data["user_id"] == "demo_user"
    assert data["flashcard_count"] == 0


def test_get_nonexistent_deck(auth_client: TestClient):  # ← Changed
    """Test getting a deck that doesn't exist."""
    response = auth_client.get("/api/v1/flashcard/decks/99999")
    assert response.status_code == 404


def test_update_deck(auth_client: TestClient):  # ← Changed
    """Test updating a deck."""
    # Create a deck
    create_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Original Name"})
    deck_id = create_response.json()["id"]

    # Update the deck
    update_response = auth_client.put(
        f"/api/v1/flashcard/decks/{deck_id}", json={"name": "Updated Name"}
    )

    assert update_response.status_code == 200
    data = update_response.json()

    assert data["id"] == deck_id
    assert data["name"] == "Updated Name"


def test_update_nonexistent_deck(auth_client: TestClient):  # ← Changed
    """Test updating a deck that doesn't exist."""
    response = auth_client.put("/api/v1/flashcard/decks/99999", json={"name": "Updated Name"})

    assert response.status_code == 404


def test_delete_deck(auth_client: TestClient):  # ← Changed
    """Test deleting a deck."""
    # Create a deck
    create_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Deck to Delete"})
    deck_id = create_response.json()["id"]

    # Delete the deck
    delete_response = auth_client.delete(f"/api/v1/flashcard/decks/{deck_id}")

    assert delete_response.status_code == 204

    # Verify it's deleted
    get_response = auth_client.get(f"/api/v1/flashcard/decks/{deck_id}")
    assert get_response.status_code == 404


def test_delete_nonexistent_deck(auth_client: TestClient):  # ← Changed
    """Test deleting a deck that doesn't exist."""
    response = auth_client.delete("/api/v1/flashcard/decks/99999")
    assert response.status_code == 404


# ===== Flashcard Tests (Nested Routes) =====


def test_create_flashcard(auth_client: TestClient):  # ← Changed
    """Test creating a flashcard with nested route."""
    # Create a deck first
    deck_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Test Deck"})
    deck_id = deck_response.json()["id"]

    # Create a flashcard (no deck_id in body - comes from URL)
    response = auth_client.post(
        f"/api/v1/flashcard/decks/{deck_id}/cards", json={"front": "行く", "back": "to go"}
    )

    assert response.status_code == 201
    data = response.json()

    assert "id" in data
    assert data["deck_id"] == deck_id
    assert data["front"] == "行く"
    assert data["back"] == "to go"
    assert data["user_id"] == "demo_user"


def test_create_flashcard_invalid_deck(auth_client: TestClient):  # ← Changed
    """Test creating a flashcard with non-existent deck."""
    response = auth_client.post(
        "/api/v1/flashcard/decks/99999/cards", json={"front": "Test", "back": "Test"}
    )

    assert response.status_code == 404


def test_get_deck_flashcards(auth_client: TestClient):  # ← Changed
    """Test getting all flashcards in a deck."""
    # Create a deck
    deck_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Test Deck"})
    deck_id = deck_response.json()["id"]

    # Create multiple flashcards
    auth_client.post(
        f"/api/v1/flashcard/decks/{deck_id}/cards", json={"front": "行く", "back": "to go"}
    )
    auth_client.post(
        f"/api/v1/flashcard/decks/{deck_id}/cards", json={"front": "食べる", "back": "to eat"}
    )

    # Get flashcards
    response = auth_client.get(f"/api/v1/flashcard/decks/{deck_id}/cards")

    assert response.status_code == 200
    data = response.json()

    assert "flashcards" in data
    assert "total_count" in data
    assert data["total_count"] == 2
    assert len(data["flashcards"]) == 2


def test_get_flashcard(auth_client: TestClient):  # ← Changed
    """Test getting a specific flashcard."""
    # Create a deck and flashcard
    deck_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Test Deck"})
    deck_id = deck_response.json()["id"]

    card_response = auth_client.post(
        f"/api/v1/flashcard/decks/{deck_id}/cards", json={"front": "行く", "back": "to go"}
    )
    card_id = card_response.json()["id"]

    # Get the flashcard
    response = auth_client.get(f"/api/v1/flashcard/decks/{deck_id}/cards/{card_id}")

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == card_id
    assert data["deck_id"] == deck_id
    assert data["front"] == "行く"
    assert data["back"] == "to go"


def test_get_flashcard_wrong_deck(auth_client: TestClient):  # ← Changed
    """Test getting a flashcard from wrong deck returns 404."""
    # Create two decks
    deck1_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Deck 1"})
    deck1_id = deck1_response.json()["id"]

    deck2_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Deck 2"})
    deck2_id = deck2_response.json()["id"]

    # Create flashcard in deck 1
    card_response = auth_client.post(
        f"/api/v1/flashcard/decks/{deck1_id}/cards", json={"front": "Test", "back": "Test"}
    )
    card_id = card_response.json()["id"]

    # Try to get flashcard from deck 2 (should fail)
    response = auth_client.get(f"/api/v1/flashcard/decks/{deck2_id}/cards/{card_id}")
    assert response.status_code == 404


def test_update_flashcard(auth_client: TestClient):  # ← Changed
    """Test updating a flashcard."""
    # Create a deck and flashcard
    deck_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Test Deck"})
    deck_id = deck_response.json()["id"]

    card_response = auth_client.post(
        f"/api/v1/flashcard/decks/{deck_id}/cards", json={"front": "Original", "back": "Original"}
    )
    card_id = card_response.json()["id"]

    # Update the flashcard
    update_response = auth_client.put(
        f"/api/v1/flashcard/decks/{deck_id}/cards/{card_id}",
        json={"front": "Updated Front", "back": "Updated Back"},
    )

    assert update_response.status_code == 200
    data = update_response.json()

    assert data["id"] == card_id
    assert data["front"] == "Updated Front"
    assert data["back"] == "Updated Back"


def test_update_flashcard_partial(auth_client: TestClient):  # ← Changed
    """Test partial update of a flashcard."""
    # Create a deck and flashcard
    deck_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Test Deck"})
    deck_id = deck_response.json()["id"]

    card_response = auth_client.post(
        f"/api/v1/flashcard/decks/{deck_id}/cards",
        json={"front": "Original Front", "back": "Original Back"},
    )
    card_id = card_response.json()["id"]

    # Update only back
    update_response = auth_client.put(
        f"/api/v1/flashcard/decks/{deck_id}/cards/{card_id}", json={"back": "Updated Back"}
    )

    assert update_response.status_code == 200
    data = update_response.json()

    assert data["front"] == "Original Front"  # Unchanged
    assert data["back"] == "Updated Back"  # Changed


def test_update_flashcard_wrong_deck(auth_client: TestClient):  # ← Changed
    """Test updating a flashcard from wrong deck returns 404."""
    # Create two decks
    deck1_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Deck 1"})
    deck1_id = deck1_response.json()["id"]

    deck2_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Deck 2"})
    deck2_id = deck2_response.json()["id"]

    # Create flashcard in deck 1
    card_response = auth_client.post(
        f"/api/v1/flashcard/decks/{deck1_id}/cards", json={"front": "Test", "back": "Test"}
    )
    card_id = card_response.json()["id"]

    # Try to update flashcard via deck 2 (should fail)
    response = auth_client.put(
        f"/api/v1/flashcard/decks/{deck2_id}/cards/{card_id}", json={"back": "Updated"}
    )
    assert response.status_code == 404


def test_delete_flashcard(auth_client: TestClient):  # ← Changed
    """Test deleting a flashcard."""
    # Create a deck and flashcard
    deck_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Test Deck"})
    deck_id = deck_response.json()["id"]

    card_response = auth_client.post(
        f"/api/v1/flashcard/decks/{deck_id}/cards", json={"front": "Delete Me", "back": "Delete Me"}
    )
    card_id = card_response.json()["id"]

    # Delete the flashcard
    delete_response = auth_client.delete(f"/api/v1/flashcard/decks/{deck_id}/cards/{card_id}")

    assert delete_response.status_code == 204

    # Verify it's deleted
    get_response = auth_client.get(f"/api/v1/flashcard/decks/{deck_id}/cards/{card_id}")
    assert get_response.status_code == 404


def test_delete_flashcard_wrong_deck(auth_client: TestClient):  # ← Changed
    """Test deleting a flashcard from wrong deck returns 404."""
    # Create two decks
    deck1_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Deck 1"})
    deck1_id = deck1_response.json()["id"]

    deck2_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Deck 2"})
    deck2_id = deck2_response.json()["id"]

    # Create flashcard in deck 1
    card_response = auth_client.post(
        f"/api/v1/flashcard/decks/{deck1_id}/cards", json={"front": "Test", "back": "Test"}
    )
    card_id = card_response.json()["id"]

    # Try to delete flashcard via deck 2 (should fail)
    response = auth_client.delete(f"/api/v1/flashcard/decks/{deck2_id}/cards/{card_id}")
    assert response.status_code == 404


def test_delete_deck_with_flashcards(auth_client: TestClient):  # ← Changed
    """Test deleting a deck that contains flashcards (cascade delete)."""
    # Create a deck
    deck_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Deck with Cards"})
    deck_id = deck_response.json()["id"]

    # Add flashcards
    card1 = auth_client.post(
        f"/api/v1/flashcard/decks/{deck_id}/cards", json={"front": "Card 1", "back": "Card 1"}
    ).json()

    auth_client.post(
        f"/api/v1/flashcard/decks/{deck_id}/cards", json={"front": "Card 2", "back": "Card 2"}
    )

    # Delete the deck
    delete_response = auth_client.delete(f"/api/v1/flashcard/decks/{deck_id}")

    assert delete_response.status_code == 204

    # Verify deck is deleted
    get_deck_response = auth_client.get(f"/api/v1/flashcard/decks/{deck_id}")
    assert get_deck_response.status_code == 404

    # Verify flashcards are also deleted
    get_card1_response = auth_client.get(f"/api/v1/flashcard/decks/{deck_id}/cards/{card1['id']}")
    assert get_card1_response.status_code == 404


# ===== Service Layer Tests =====


def test_flashcard_service_create_deck(session: Session):
    """Test FlashcardService create_deck method."""
    service = FlashcardService(session)

    deck_create = DeckCreate(name="Service Test Deck")
    deck = service.create_deck("test_user", deck_create)

    assert deck.id is not None
    assert deck.name == "Service Test Deck"
    assert deck.user_id == "test_user"
    assert deck.flashcard_count == 0


def test_flashcard_service_get_deck(session: Session):
    """Test FlashcardService get_deck method."""
    service = FlashcardService(session)

    # Create a deck
    deck_create = DeckCreate(name="Test Deck")
    created_deck = service.create_deck("test_user", deck_create)

    # Get the deck
    deck = service.get_deck(created_deck.id, "test_user")

    assert deck.id == created_deck.id
    assert deck.name == "Test Deck"
    assert deck.user_id == "test_user"


def test_flashcard_service_create_flashcard(session: Session):
    """Test FlashcardService create_flashcard method."""
    service = FlashcardService(session)

    # Create a deck first
    deck_create = DeckCreate(name="Test Deck")
    deck = service.create_deck("test_user", deck_create)

    # Create a flashcard
    flashcard_create = FlashcardCreate(deck_id=deck.id, front="Test Front", back="Test Back")
    flashcard = service.create_flashcard("test_user", flashcard_create)

    assert flashcard.id is not None
    assert flashcard.deck_id == deck.id
    assert flashcard.front == "Test Front"
    assert flashcard.back == "Test Back"
    assert flashcard.user_id == "test_user"


def test_flashcard_service_validation_error(session: Session):
    """Test FlashcardService raises ValidationException for invalid deck."""
    service = FlashcardService(session)

    flashcard_create = FlashcardCreate(deck_id=99999, front="Test", back="Test")

    with pytest.raises(ValidationException):
        service.create_flashcard("test_user", flashcard_create)


def test_flashcard_service_user_isolation(session: Session):
    """Test that users can only access their own data."""
    service = FlashcardService(session)

    # User A creates a deck
    deck_create = DeckCreate(name="User A Deck")
    deck = service.create_deck("user_a", deck_create)

    # User B tries to access User A's deck
    with pytest.raises(ValidationException):
        service.get_deck(deck.id, "user_b")


# ===== Integration Tests =====


def test_full_flashcard_workflow(auth_client: TestClient):  # ← Changed
    """Test complete workflow: create deck, add cards, update, delete."""
    # 1. Create a deck
    deck_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Japanese N5"})
    assert deck_response.status_code == 201
    deck_id = deck_response.json()["id"]

    # 2. Add flashcards (using nested route)
    card1 = auth_client.post(
        f"/api/v1/flashcard/decks/{deck_id}/cards", json={"front": "行く", "back": "to go"}
    ).json()

    card2 = auth_client.post(
        f"/api/v1/flashcard/decks/{deck_id}/cards", json={"front": "食べる", "back": "to eat"}
    ).json()

    # 3. Verify flashcards were added
    cards_response = auth_client.get(f"/api/v1/flashcard/decks/{deck_id}/cards")
    assert cards_response.json()["total_count"] == 2

    # 4. Update a flashcard
    update_response = auth_client.put(
        f"/api/v1/flashcard/decks/{deck_id}/cards/{card1['id']}", json={"back": "to go (updated)"}
    )
    assert update_response.json()["back"] == "to go (updated)"

    # 5. Delete a flashcard
    delete_card_response = auth_client.delete(
        f"/api/v1/flashcard/decks/{deck_id}/cards/{card2['id']}"
    )
    assert delete_card_response.status_code == 204

    # 6. Verify only 1 card remains
    cards_response = auth_client.get(f"/api/v1/flashcard/decks/{deck_id}/cards")
    assert cards_response.json()["total_count"] == 1

    # 7. Update deck name
    update_deck_response = auth_client.put(
        f"/api/v1/flashcard/decks/{deck_id}", json={"name": "Japanese N5 (Updated)"}
    )
    assert update_deck_response.json()["name"] == "Japanese N5 (Updated)"

    # 8. Delete entire deck
    delete_deck_response = auth_client.delete(f"/api/v1/flashcard/decks/{deck_id}")
    assert delete_deck_response.status_code == 204


def test_deck_flashcard_count_updates(auth_client: TestClient):  # ← Changed
    """Test that deck's flashcard_count updates correctly."""
    # Create deck
    deck_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Count Test Deck"})
    deck_id = deck_response.json()["id"]

    # Check initial count
    deck = auth_client.get(f"/api/v1/flashcard/decks/{deck_id}").json()
    assert deck["flashcard_count"] == 0

    # Add flashcards
    auth_client.post(f"/api/v1/flashcard/decks/{deck_id}/cards", json={"front": "1", "back": "1"})
    auth_client.post(f"/api/v1/flashcard/decks/{deck_id}/cards", json={"front": "2", "back": "2"})

    # Check count after adding
    deck = auth_client.get(f"/api/v1/flashcard/decks/{deck_id}").json()
    assert deck["flashcard_count"] == 2


def test_multiple_decks_isolation(auth_client: TestClient):  # ← Changed
    """Test that flashcards are isolated between decks."""
    # Create two decks
    deck1 = auth_client.post("/api/v1/flashcard/decks", json={"name": "Deck 1"}).json()

    deck2 = auth_client.post("/api/v1/flashcard/decks", json={"name": "Deck 2"}).json()

    # Add flashcards to deck 1
    auth_client.post(
        f"/api/v1/flashcard/decks/{deck1['id']}/cards",
        json={"front": "Deck 1 Card", "back": "Deck 1 Card"},
    )

    # Add flashcards to deck 2
    auth_client.post(
        f"/api/v1/flashcard/decks/{deck2['id']}/cards",
        json={"front": "Deck 2 Card", "back": "Deck 2 Card"},
    )

    # Verify deck 1 has only its cards
    deck1_cards = auth_client.get(f"/api/v1/flashcard/decks/{deck1['id']}/cards").json()
    assert deck1_cards["total_count"] == 1
    assert deck1_cards["flashcards"][0]["front"] == "Deck 1 Card"

    # Verify deck 2 has only its cards
    deck2_cards = auth_client.get(f"/api/v1/flashcard/decks/{deck2['id']}/cards").json()
    assert deck2_cards["total_count"] == 1
    assert deck2_cards["flashcards"][0]["front"] == "Deck 2 Card"


# ===== Validation Tests =====


def test_create_deck_empty_name(auth_client: TestClient):  # ← Changed
    """Test creating a deck with empty name fails validation."""
    response = auth_client.post("/api/v1/flashcard/decks", json={"name": ""})
    assert response.status_code == 422


def test_create_flashcard_empty_fields(auth_client: TestClient):  # ← Changed
    """Test creating a flashcard with empty fields fails validation."""
    deck_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Test Deck"})
    deck_id = deck_response.json()["id"]

    # Empty front
    response = auth_client.post(
        f"/api/v1/flashcard/decks/{deck_id}/cards", json={"front": "", "back": "test"}
    )
    assert response.status_code == 422

    # Empty back
    response = auth_client.post(
        f"/api/v1/flashcard/decks/{deck_id}/cards", json={"front": "test", "back": ""}
    )
    assert response.status_code == 422


def test_update_flashcard_long_text(auth_client: TestClient):  # ← Changed
    """Test updating flashcard with very long text."""
    deck_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Test Deck"})
    deck_id = deck_response.json()["id"]

    card_response = auth_client.post(
        f"/api/v1/flashcard/decks/{deck_id}/cards", json={"front": "Test", "back": "Test"}
    )
    card_id = card_response.json()["id"]

    # Text within limit (1000 chars) should work
    long_text = "a" * 1000
    response = auth_client.put(
        f"/api/v1/flashcard/decks/{deck_id}/cards/{card_id}", json={"back": long_text}
    )
    assert response.status_code == 200

    # Text over limit should fail
    too_long_text = "a" * 1001
    response = auth_client.put(
        f"/api/v1/flashcard/decks/{deck_id}/cards/{card_id}", json={"back": too_long_text}
    )
    assert response.status_code == 422


# ===== Add test for unauthenticated access =====


def test_flashcard_requires_auth(client: TestClient):  # ← New test
    """Test that flashcard endpoints require authentication."""
    response = client.get("/api/v1/flashcard/decks")
    assert response.status_code == 403
