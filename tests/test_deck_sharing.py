"""Tests for deck sharing functionality."""

from fastapi.testclient import TestClient
from sqlmodel import Session

from src.suca.db.model import Flashcard, FlashcardDeck

# Helper to get test user ID
TEST_USER_ID = "demo_user"


def test_create_public_deck(auth_client: TestClient):
    """Test creating a public deck."""
    response = auth_client.post(
        "/api/v1/flashcard/decks",
        json={
            "name": "Public Spanish Deck",
            "description": "Basic Spanish vocabulary for beginners",
            "is_public": True,
        },
    )

    assert response.status_code == 201  # Created
    data = response.json()
    assert data["name"] == "Public Spanish Deck"
    assert data["description"] == "Basic Spanish vocabulary for beginners"
    assert data["is_public"] is True


def test_update_deck_to_public(auth_client: TestClient, session: Session):
    """Test making a private deck public."""
    # Create a private deck first
    deck = FlashcardDeck(user_id=TEST_USER_ID, name="Test Deck", is_public=False)
    session.add(deck)
    session.commit()
    session.refresh(deck)

    # Make deck public
    response = auth_client.patch(
        f"/api/v1/flashcard/decks/{deck.id}",
        json={"is_public": True, "description": "Shared with the community"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_public"] is True
    assert data["description"] == "Shared with the community"


def test_list_public_decks_no_auth(client: TestClient, session: Session):
    """Test listing public decks without authentication."""
    # Create some public and private decks
    public_deck1 = FlashcardDeck(
        user_id=TEST_USER_ID,
        name="Public Deck 1",
        description="First public deck",
        is_public=True,
    )
    public_deck2 = FlashcardDeck(
        user_id=TEST_USER_ID,
        name="Public Deck 2",
        description="Second public deck",
        is_public=True,
    )
    private_deck = FlashcardDeck(
        user_id=TEST_USER_ID,
        name="Private Deck",
        is_public=False,
    )
    session.add_all([public_deck1, public_deck2, private_deck])
    session.commit()

    # List public decks without auth
    response = client.get("/api/v1/flashcard/public/decks")

    assert response.status_code == 200
    data = response.json()
    assert "decks" in data

    # Should only return public decks
    deck_names = [d["name"] for d in data["decks"]]
    assert "Public Deck 1" in deck_names
    assert "Public Deck 2" in deck_names
    assert "Private Deck" not in deck_names


def test_get_public_deck_no_auth(client: TestClient, session: Session):
    """Test getting a public deck without authentication."""
    # Create a public deck
    public_deck = FlashcardDeck(
        user_id=TEST_USER_ID,
        name="Spanish Basics",
        description="Learn Spanish basics",
        is_public=True,
    )
    session.add(public_deck)
    session.commit()
    session.refresh(public_deck)

    # Get public deck without auth
    response = client.get(f"/api/v1/flashcard/public/decks/{public_deck.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Spanish Basics"
    assert data["description"] == "Learn Spanish basics"
    assert data["is_public"] is True


def test_get_private_deck_as_public_fails(client: TestClient, session: Session):
    """Test that private decks cannot be accessed via public endpoint."""
    # Create a private deck
    private_deck = FlashcardDeck(
        user_id=TEST_USER_ID,
        name="Private Deck",
        is_public=False,
    )
    session.add(private_deck)
    session.commit()
    session.refresh(private_deck)

    # Try to get private deck via public endpoint
    response = client.get(f"/api/v1/flashcard/public/decks/{private_deck.id}")

    assert response.status_code == 404


def test_get_public_deck_flashcards_no_auth(client: TestClient, session: Session):
    """Test getting flashcards from a public deck without authentication."""
    # Create a public deck with flashcards
    public_deck = FlashcardDeck(
        user_id=TEST_USER_ID,
        name="Spanish Basics",
        is_public=True,
    )
    session.add(public_deck)
    session.commit()
    session.refresh(public_deck)

    # Add flashcards
    flashcard1 = Flashcard(
        deck_id=public_deck.id,
        user_id=TEST_USER_ID,
        front="Hola",
        back="Hello",
    )
    flashcard2 = Flashcard(
        deck_id=public_deck.id,
        user_id=TEST_USER_ID,
        front="Adiós",
        back="Goodbye",
    )
    session.add_all([flashcard1, flashcard2])
    session.commit()

    # Get flashcards without auth
    response = client.get(f"/api/v1/flashcard/public/decks/{public_deck.id}/cards")

    assert response.status_code == 200
    data = response.json()
    assert "flashcards" in data
    assert len(data["flashcards"]) == 2

    fronts = [fc["front"] for fc in data["flashcards"]]
    assert "Hola" in fronts
    assert "Adiós" in fronts


def test_copy_public_deck(auth_client: TestClient, session: Session):
    """Test copying a public deck to user's collection."""
    # Create a public deck with flashcards
    public_deck = FlashcardDeck(
        user_id="other_user_id",  # Different user
        name="Spanish Basics",
        description="Community shared deck",
        is_public=True,
    )
    session.add(public_deck)
    session.commit()
    session.refresh(public_deck)

    # Add flashcards
    flashcard1 = Flashcard(
        deck_id=public_deck.id,
        user_id="other_user_id",
        front="Hola",
        back="Hello",
    )
    flashcard2 = Flashcard(
        deck_id=public_deck.id,
        user_id="other_user_id",
        front="Gracias",
        back="Thank you",
    )
    session.add_all([flashcard1, flashcard2])
    session.commit()

    # Copy deck to current user
    response = auth_client.post(f"/api/v1/flashcard/decks/{public_deck.id}/copy")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Spanish Basics (Copy)"
    assert data["description"] == "Community shared deck"
    assert data["is_public"] is False  # Copied decks are private
    assert data["user_id"] == TEST_USER_ID  # Owned by current user
    assert data["flashcard_count"] == 2


def test_copy_public_deck_with_custom_name(auth_client: TestClient, session: Session):
    """Test copying a public deck with a custom name."""
    # Create a public deck
    public_deck = FlashcardDeck(
        user_id="other_user_id",
        name="Spanish Basics",
        is_public=True,
    )
    session.add(public_deck)
    session.commit()
    session.refresh(public_deck)

    # Copy with custom name
    response = auth_client.post(
        f"/api/v1/flashcard/decks/{public_deck.id}/copy?new_name=My Spanish Deck"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "My Spanish Deck"


def test_copy_private_deck_fails(auth_client: TestClient, session: Session):
    """Test that private decks cannot be copied."""
    # Create a private deck
    private_deck = FlashcardDeck(
        user_id="other_user_id",
        name="Private Deck",
        is_public=False,
    )
    session.add(private_deck)
    session.commit()
    session.refresh(private_deck)

    # Try to copy private deck
    response = auth_client.post(f"/api/v1/flashcard/decks/{private_deck.id}/copy")

    assert response.status_code == 404


def test_copy_nonexistent_deck_fails(auth_client: TestClient):
    """Test that copying a nonexistent deck fails."""
    response = auth_client.post("/api/v1/flashcard/decks/99999/copy")

    assert response.status_code == 404


def test_copy_deck_requires_auth(client: TestClient, session: Session):
    """Test that copying a deck requires authentication."""
    # Create a public deck
    public_deck = FlashcardDeck(
        user_id=TEST_USER_ID,
        name="Public Deck",
        is_public=True,
    )
    session.add(public_deck)
    session.commit()
    session.refresh(public_deck)

    # Try to copy without auth
    response = client.post(f"/api/v1/flashcard/decks/{public_deck.id}/copy")

    assert response.status_code == 403  # Forbidden (not authenticated)
