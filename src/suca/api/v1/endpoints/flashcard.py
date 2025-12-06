"""Flashcard endpoints."""

import csv
import io
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from ....api.deps import get_session
from ....core.auth import get_current_user_id
from ....core.exceptions import DatabaseException, ValidationException
from ....schemas.flashcard_schemas import (
    BulkCreateRequest,
    BulkDeleteRequest,
    BulkMoveRequest,
    BulkOperationResponse,
    BulkResetRequest,
    BulkUpdateRequest,
    DeckCreate,
    DeckListResponse,
    DeckResponse,
    DeckUpdate,
    DueCardsResponse,
    FlashcardCreate,
    FlashcardCreateNested,
    FlashcardListResponse,
    FlashcardResponse,
    FlashcardReviewRequest,
    FlashcardReviewResponse,
    FlashcardUpdate,
)
from ....services.flashcard_service import FlashcardService

router = APIRouter(prefix="/flashcard", tags=["Flashcard"])


def get_flashcard_service(session: Session = Depends(get_session)) -> FlashcardService:
    """Get flashcard service instance."""
    return FlashcardService(session)


# Type aliases for dependencies
UserIdDep = Annotated[str, Depends(get_current_user_id)]
FlashcardServiceDep = Annotated[FlashcardService, Depends(get_flashcard_service)]


# ===== Deck Endpoints =====


@router.get("/decks", response_model=DeckListResponse)
def list_flashcard_decks(
    user_id: UserIdDep, flashcard_service: FlashcardServiceDep
) -> DeckListResponse:
    """Get all decks for current user. Requires authentication."""
    try:
        return flashcard_service.get_user_decks(user_id)
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decks", response_model=DeckResponse, status_code=201)
def create_flashcard_deck(
    deck: DeckCreate, user_id: UserIdDep, flashcard_service: FlashcardServiceDep
) -> DeckResponse:
    """Create a new flashcard deck. Requires authentication."""
    try:
        return flashcard_service.create_deck(user_id, deck)
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decks/{deck_id}", response_model=DeckResponse)
def get_flashcard_deck(
    deck_id: int, user_id: UserIdDep, flashcard_service: FlashcardServiceDep
) -> DeckResponse:
    """Get a specific deck. Requires authentication."""
    try:
        return flashcard_service.get_deck(deck_id, user_id)
    except ValidationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/decks/{deck_id}", response_model=DeckResponse)
@router.patch("/decks/{deck_id}", response_model=DeckResponse)
def update_flashcard_deck(
    deck_id: int,
    deck_update: DeckUpdate,
    user_id: UserIdDep,
    flashcard_service: FlashcardServiceDep,
) -> DeckResponse:
    """Update a flashcard deck. Requires authentication."""
    try:
        return flashcard_service.update_deck(deck_id, user_id, deck_update)
    except ValidationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/decks/{deck_id}", status_code=204)
def delete_flashcard_deck(deck_id: int, user_id: UserIdDep, flashcard_service: FlashcardServiceDep):
    """Delete a flashcard deck and all its cards. Requires authentication."""
    try:
        flashcard_service.delete_deck(deck_id, user_id)
    except ValidationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Flashcard Endpoints (Nested under Decks) =====


@router.get("/decks/{deck_id}/cards", response_model=FlashcardListResponse)
def get_flashcards(
    deck_id: int, user_id: UserIdDep, flashcard_service: FlashcardServiceDep
) -> FlashcardListResponse:
    """Get all flashcards in a deck. Requires authentication."""
    try:
        return flashcard_service.get_deck_flashcards(deck_id, user_id)
    except ValidationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decks/{deck_id}/cards", response_model=FlashcardResponse, status_code=201)
def add_flashcard(
    deck_id: int,
    flashcard: FlashcardCreateNested,
    user_id: UserIdDep,
    flashcard_service: FlashcardServiceDep,
) -> FlashcardResponse:
    """Add a new flashcard to a deck. Requires authentication."""
    try:
        flashcard_with_deck = FlashcardCreate(
            deck_id=deck_id, front=flashcard.front, back=flashcard.back
        )
        return flashcard_service.create_flashcard(user_id, flashcard_with_deck)
    except ValidationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decks/{deck_id}/cards/{card_id}", response_model=FlashcardResponse)
def get_flashcard(
    deck_id: int, card_id: int, user_id: UserIdDep, flashcard_service: FlashcardServiceDep
) -> FlashcardResponse:
    """Get a specific flashcard. Requires authentication."""
    try:
        flashcard = flashcard_service.get_flashcard(card_id, user_id)

        if flashcard.deck_id != deck_id:
            raise HTTPException(
                status_code=404, detail=f"Flashcard {card_id} not found in deck {deck_id}"
            )

        return flashcard
    except ValidationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/decks/{deck_id}/cards/{card_id}", response_model=FlashcardResponse)
def update_flashcard(
    deck_id: int,
    card_id: int,
    flashcard_update: FlashcardUpdate,
    user_id: UserIdDep,
    flashcard_service: FlashcardServiceDep,
) -> FlashcardResponse:
    """Update a flashcard. Requires authentication."""
    try:
        flashcard = flashcard_service.get_flashcard(card_id, user_id)

        if flashcard.deck_id != deck_id:
            raise HTTPException(
                status_code=404, detail=f"Flashcard {card_id} not found in deck {deck_id}"
            )

        return flashcard_service.update_flashcard(card_id, user_id, flashcard_update)
    except ValidationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/decks/{deck_id}/cards/{card_id}", status_code=204)
def delete_flashcard(
    deck_id: int, card_id: int, user_id: UserIdDep, flashcard_service: FlashcardServiceDep
):
    """Delete a flashcard. Requires authentication."""
    try:
        flashcard = flashcard_service.get_flashcard(card_id, user_id)

        if flashcard.deck_id != deck_id:
            raise HTTPException(
                status_code=404, detail=f"Flashcard {card_id} not found in deck {deck_id}"
            )

        flashcard_service.delete_flashcard(card_id, user_id)
    except ValidationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decks/{deck_id}/cards/bulk-delete")
def bulk_delete_flashcards(
    deck_id: int,
    request: BulkDeleteRequest,
    user_id: UserIdDep,
    flashcard_service: FlashcardServiceDep,
) -> BulkOperationResponse:
    """Delete multiple flashcards at once. Requires authentication."""
    try:
        return flashcard_service.bulk_delete_flashcards(deck_id, user_id, request)
    except ValidationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decks/{deck_id}/cards/bulk-create", status_code=201)
def bulk_create_flashcards(
    deck_id: int,
    request: BulkCreateRequest,
    user_id: UserIdDep,
    flashcard_service: FlashcardServiceDep,
) -> BulkOperationResponse:
    """Create multiple flashcards at once (max 100). Requires authentication."""
    try:
        return flashcard_service.bulk_create_flashcards(deck_id, user_id, request)
    except ValidationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decks/{deck_id}/cards/bulk-update")
def bulk_update_flashcards(
    deck_id: int,
    request: BulkUpdateRequest,
    user_id: UserIdDep,
    flashcard_service: FlashcardServiceDep,
) -> BulkOperationResponse:
    """Update multiple flashcards at once (max 100). Requires authentication."""
    try:
        return flashcard_service.bulk_update_flashcards(deck_id, user_id, request)
    except ValidationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decks/{deck_id}/cards/bulk-move")
def bulk_move_flashcards(
    deck_id: int,
    request: BulkMoveRequest,
    user_id: UserIdDep,
    flashcard_service: FlashcardServiceDep,
) -> BulkOperationResponse:
    """Move multiple flashcards to another deck. Requires authentication."""
    try:
        return flashcard_service.bulk_move_flashcards(deck_id, user_id, request)
    except ValidationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decks/{deck_id}/cards/bulk-reset")
def bulk_reset_flashcards(
    deck_id: int,
    request: BulkResetRequest,
    user_id: UserIdDep,
    flashcard_service: FlashcardServiceDep,
) -> BulkOperationResponse:
    """Reset FSRS state for multiple flashcards (back to new). Requires authentication."""
    try:
        return flashcard_service.bulk_reset_flashcards(deck_id, user_id, request)
    except ValidationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== FSRS Review Endpoints =====


@router.post("/decks/{deck_id}/cards/{card_id}/review", response_model=FlashcardReviewResponse)
def review_flashcard(
    deck_id: int,
    card_id: int,
    review: FlashcardReviewRequest,
    user_id: UserIdDep,
    flashcard_service: FlashcardServiceDep,
) -> FlashcardReviewResponse:
    """
    Review a flashcard with FSRS rating.

    Rating values:
    - 1 = Again (forgot completely)
    - 2 = Hard (remembered with difficulty)
    - 3 = Good (remembered correctly)
    - 4 = Easy (remembered instantly)

    Requires authentication.
    """
    try:
        flashcard = flashcard_service.get_flashcard(card_id, user_id)

        if flashcard.deck_id != deck_id:
            raise HTTPException(
                status_code=404, detail=f"Flashcard {card_id} not found in deck {deck_id}"
            )

        return flashcard_service.review_flashcard(card_id, user_id, review)
    except ValidationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/due", response_model=DueCardsResponse)
def get_due_cards(user_id: UserIdDep, flashcard_service: FlashcardServiceDep) -> DueCardsResponse:
    """
    Get all cards due for review across all decks.

    Returns statistics including:
    - Total cards per deck
    - New/Learning/Review card counts
    - Cards currently due for review

    Requires authentication.
    """
    try:
        return flashcard_service.get_due_cards(user_id)
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== CSV Import/Export Endpoints =====


@router.get("/decks/{deck_id}/export/csv")
def export_deck_csv(
    deck_id: int, user_id: UserIdDep, flashcard_service: FlashcardServiceDep
) -> StreamingResponse:
    """
    Export a flashcard deck to CSV format.

    Returns a CSV file with columns: front, back
    The file can be downloaded and used for backup or importing into other systems.

    Requires authentication.
    """
    try:
        # Verify deck ownership
        deck = flashcard_service.get_deck(deck_id, user_id)

        # Get all flashcards in the deck
        flashcards_response = flashcard_service.get_deck_flashcards(deck_id, user_id)

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(["front", "back"])

        # Write flashcard data
        for flashcard in flashcards_response.flashcards:
            writer.writerow([flashcard.front, flashcard.back])

        # Prepare response
        output.seek(0)

        # Create filename from deck name (sanitize for filesystem)
        safe_filename = "".join(
            c if c.isalnum() or c in (" ", "-", "_") else "_" for c in deck.name
        )
        filename = f"{safe_filename}.csv"

        return StreamingResponse(
            io.BytesIO(
                output.getvalue().encode("utf-8-sig")
            ),  # UTF-8 with BOM for Excel compatibility
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except ValidationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decks/{deck_id}/import/csv")
async def import_deck_csv(
    deck_id: int,
    user_id: UserIdDep,
    flashcard_service: FlashcardServiceDep,
    file: UploadFile = File(...),
):
    """
    Import flashcards from CSV file into a deck.

    Expected CSV format:
    - Header row: front, back
    - Each subsequent row: front_text, back_text

    Notes:
    - Duplicates are not checked - all rows will be imported as new cards
    - Empty rows are skipped
    - Maximum file size: 10MB

    Requires authentication.
    """
    try:
        # Verify deck ownership
        flashcard_service.get_deck(deck_id, user_id)

        # Check file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file uploaded")

        if not file.filename.endswith(".csv"):
            raise HTTPException(status_code=400, detail="File must be a CSV file")

        # Read file content
        content = await file.read()

        # Check file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(content) > max_size:
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")

        # Parse CSV
        try:
            decoded_content = content.decode("utf-8-sig")  # Handle UTF-8 BOM
        except UnicodeDecodeError:
            try:
                decoded_content = content.decode("utf-8")
            except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail="File must be UTF-8 encoded")

        csv_reader = csv.DictReader(io.StringIO(decoded_content))

        # Validate header
        if (
            not csv_reader.fieldnames
            or "front" not in csv_reader.fieldnames
            or "back" not in csv_reader.fieldnames
        ):
            raise HTTPException(
                status_code=400, detail="CSV must have 'front' and 'back' columns in header"
            )

        # Import flashcards
        imported_count = 0
        skipped_count = 0

        for row in csv_reader:
            front = row.get("front", "").strip()
            back = row.get("back", "").strip()

            # Skip empty rows
            if not front or not back:
                skipped_count += 1
                continue

            # Create flashcard
            flashcard_create = FlashcardCreate(deck_id=deck_id, front=front, back=back)
            flashcard_service.create_flashcard(user_id, flashcard_create)
            imported_count += 1

        return {
            "success": True,
            "imported_count": imported_count,
            "skipped_count": skipped_count,
            "message": f"Successfully imported {imported_count} flashcards",
        }

    except ValidationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except csv.Error as e:
        raise HTTPException(status_code=400, detail=f"Invalid CSV format: {str(e)}")


# ===== Public Deck Endpoints (No Auth Required) =====


@router.get("/public/decks", response_model=DeckListResponse)
def list_public_decks(
    flashcard_service: FlashcardServiceDep, limit: int = 50, offset: int = 0
) -> DeckListResponse:
    """Get all public (shared) decks. No authentication required."""
    try:
        return flashcard_service.get_public_decks(limit=limit, offset=offset)
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/public/decks/{deck_id}", response_model=DeckResponse)
def get_public_deck(deck_id: int, flashcard_service: FlashcardServiceDep) -> DeckResponse:
    """Get a public deck by ID. No authentication required."""
    try:
        return flashcard_service.get_public_deck(deck_id)
    except ValidationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/public/decks/{deck_id}/cards", response_model=FlashcardListResponse)
def get_public_deck_flashcards(
    deck_id: int, flashcard_service: FlashcardServiceDep
) -> FlashcardListResponse:
    """Get all flashcards from a public deck. No authentication required."""
    try:
        return flashcard_service.get_public_deck_flashcards(deck_id)
    except ValidationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decks/{deck_id}/copy", response_model=DeckResponse)
def copy_public_deck(
    deck_id: int,
    user_id: UserIdDep,
    flashcard_service: FlashcardServiceDep,
    new_name: str | None = None,
) -> DeckResponse:
    """Copy a public deck to user's collection. Requires authentication."""
    try:
        return flashcard_service.copy_deck_to_user(deck_id, user_id, new_name)
    except ValidationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))
