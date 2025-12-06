"""Tests for CSV import/export functionality."""

import io

from fastapi.testclient import TestClient


def test_export_deck_csv(auth_client: TestClient):
    """Test exporting a deck to CSV format."""
    # Create a deck
    deck_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Test Export Deck"})
    assert deck_response.status_code == 201
    deck_id = deck_response.json()["id"]

    # Add some flashcards
    flashcards = [
        {"front": "Hello", "back": "こんにちは"},
        {"front": "Goodbye", "back": "さようなら"},
        {"front": "Thank you", "back": "ありがとう"},
    ]

    for card in flashcards:
        response = auth_client.post(f"/api/v1/flashcard/decks/{deck_id}/cards", json=card)
        assert response.status_code == 201

    # Export to CSV
    response = auth_client.get(f"/api/v1/flashcard/decks/{deck_id}/export/csv")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]

    # Parse CSV content
    content = response.content.decode("utf-8-sig")
    lines = [line.strip() for line in content.strip().split("\n")]

    # Check header
    assert lines[0] == "front,back"

    # Check data rows
    assert len(lines) == 4  # header + 3 cards
    assert "Hello" in content
    assert "こんにちは" in content


def test_export_empty_deck(auth_client: TestClient):
    """Test exporting an empty deck."""
    # Create an empty deck
    deck_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Empty Deck"})
    assert deck_response.status_code == 201
    deck_id = deck_response.json()["id"]

    # Export to CSV
    response = auth_client.get(f"/api/v1/flashcard/decks/{deck_id}/export/csv")

    assert response.status_code == 200
    content = response.content.decode("utf-8-sig")
    lines = content.strip().split("\n")

    # Should only have header
    assert len(lines) == 1
    assert lines[0] == "front,back"


def test_export_nonexistent_deck(auth_client: TestClient):
    """Test exporting a deck that doesn't exist."""
    response = auth_client.get("/api/v1/flashcard/decks/99999/export/csv")
    assert response.status_code == 404


def test_import_deck_csv(auth_client: TestClient):
    """Test importing flashcards from CSV."""
    # Create a deck
    deck_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Test Import Deck"})
    assert deck_response.status_code == 201
    deck_id = deck_response.json()["id"]

    # Create CSV content
    csv_content = """front,back
Apple,りんご
Banana,バナナ
Orange,オレンジ
"""

    # Upload CSV
    files = {"file": ("test.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    response = auth_client.post(f"/api/v1/flashcard/decks/{deck_id}/import/csv", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["imported_count"] == 3
    assert data["skipped_count"] == 0

    # Verify cards were created
    cards_response = auth_client.get(f"/api/v1/flashcard/decks/{deck_id}/cards")
    assert cards_response.status_code == 200
    cards = cards_response.json()["flashcards"]
    assert len(cards) == 3


def test_import_csv_with_empty_rows(auth_client: TestClient):
    """Test importing CSV with empty rows (should be skipped)."""
    # Create a deck
    deck_response = auth_client.post(
        "/api/v1/flashcard/decks", json={"name": "Test Import with Empties"}
    )
    deck_id = deck_response.json()["id"]

    # CSV with empty rows
    csv_content = """front,back
Dog,犬

Cat,猫
,
Mouse,ねずみ
"""

    files = {"file": ("test.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    response = auth_client.post(f"/api/v1/flashcard/decks/{deck_id}/import/csv", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["imported_count"] == 3
    assert data["skipped_count"] == 1  # 1 row with empty field (CSV reader skips blank lines)


def test_import_csv_invalid_format(auth_client: TestClient):
    """Test importing CSV with invalid format."""
    # Create a deck
    deck_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Test Invalid CSV"})
    deck_id = deck_response.json()["id"]

    # Invalid CSV (missing required columns)
    csv_content = """word,translation
Apple,りんご
"""

    files = {"file": ("test.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    response = auth_client.post(f"/api/v1/flashcard/decks/{deck_id}/import/csv", files=files)

    assert response.status_code == 400
    assert "front" in response.json()["detail"] or "back" in response.json()["detail"]


def test_import_non_csv_file(auth_client: TestClient):
    """Test importing a non-CSV file."""
    # Create a deck
    deck_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Test Non-CSV"})
    deck_id = deck_response.json()["id"]

    # Non-CSV file
    files = {"file": ("test.txt", io.BytesIO(b"Not a CSV file"), "text/plain")}
    response = auth_client.post(f"/api/v1/flashcard/decks/{deck_id}/import/csv", files=files)

    assert response.status_code == 400
    assert "CSV" in response.json()["detail"]


def test_import_csv_with_utf8_bom(auth_client: TestClient):
    """Test importing CSV with UTF-8 BOM (Excel format)."""
    # Create a deck
    deck_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Test UTF-8 BOM"})
    deck_id = deck_response.json()["id"]

    # CSV with UTF-8 BOM
    csv_content = """front,back
Water,水
Fire,火
"""
    csv_bytes = b"\xef\xbb\xbf" + csv_content.encode("utf-8")  # Add BOM

    files = {"file": ("test.csv", io.BytesIO(csv_bytes), "text/csv")}
    response = auth_client.post(f"/api/v1/flashcard/decks/{deck_id}/import/csv", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["imported_count"] == 2


def test_roundtrip_export_import(auth_client: TestClient):
    """Test exporting a deck and importing it into another deck."""
    # Create first deck with cards
    deck1_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Source Deck"})
    deck1_id = deck1_response.json()["id"]

    cards = [
        {"front": "One", "back": "一"},
        {"front": "Two", "back": "二"},
        {"front": "Three", "back": "三"},
    ]

    for card in cards:
        auth_client.post(f"/api/v1/flashcard/decks/{deck1_id}/cards", json=card)

    # Export deck1
    export_response = auth_client.get(f"/api/v1/flashcard/decks/{deck1_id}/export/csv")
    assert export_response.status_code == 200
    csv_content = export_response.content

    # Create second deck
    deck2_response = auth_client.post("/api/v1/flashcard/decks", json={"name": "Target Deck"})
    deck2_id = deck2_response.json()["id"]

    # Import into deck2
    files = {"file": ("exported.csv", io.BytesIO(csv_content), "text/csv")}
    import_response = auth_client.post(
        f"/api/v1/flashcard/decks/{deck2_id}/import/csv", files=files
    )

    assert import_response.status_code == 200
    assert import_response.json()["imported_count"] == 3

    # Verify both decks have same cards
    deck1_cards = auth_client.get(f"/api/v1/flashcard/decks/{deck1_id}/cards").json()
    deck2_cards = auth_client.get(f"/api/v1/flashcard/decks/{deck2_id}/cards").json()

    assert len(deck1_cards["flashcards"]) == len(deck2_cards["flashcards"])

    # Compare front/back (ignore IDs and timestamps)
    deck1_pairs = {(c["front"], c["back"]) for c in deck1_cards["flashcards"]}
    deck2_pairs = {(c["front"], c["back"]) for c in deck2_cards["flashcards"]}
    assert deck1_pairs == deck2_pairs
