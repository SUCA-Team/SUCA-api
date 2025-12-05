"""Flashcard endpoints with FSRS review."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ....api.deps import SessionDep
from ....core.auth import get_current_user_id
from ....core.exceptions import DatabaseException, ValidationException
from ....schemas.flashcard_schemas import (
    DeckCreate,
    DeckListResponse,
    DeckResponse,
    DeckUpdate,
    FlashcardCreateNested,
    FlashcardListResponse,
    FlashcardResponse,
    FlashcardReviewRequest,
    FlashcardReviewResponse,
    FlashcardUpdate,
)
from ....services.flashcard_service import FlashcardService

router = APIRouter(prefix="/flashcard", tags=["Flashcard"])

# Type alias
UserIdDep = Annotated[str, Depends(get_current_user_id)]


def get_flashcard_service(session: SessionDep) -> FlashcardService:
    """Dependency to get FlashcardService."""
    return FlashcardService(session)


FlashcardServiceDep = Annotated[FlashcardService, Depends(get_flashcard_service)]


# === Deck Endpoints ===


@router.post("/decks", response_model=DeckResponse, status_code=201)
def create_deck(
    deck_data: DeckCreate, user_id: UserIdDep, flashcard_service: FlashcardServiceDep
):
    """Create a new flashcard deck. Requires authentication."""
    try:
        deck = flashcard_service.create_deck(deck_data, user_id)
        return DeckResponse.model_validate(deck)
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decks", response_model=DeckListResponse)
def get_decks(user_id: UserIdDep, flashcard_service: FlashcardServiceDep):
    """Get all flashcard decks for the authenticated user."""
    try:
        decks = flashcard_service.get_decks(user_id)
        return DeckListResponse(
            decks=[DeckResponse.model_validate(d) for d in decks], total_count=len(decks)
        )
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decks/{deck_id}", response_model=DeckResponse)
def get_deck(deck_id: int, user_id: UserIdDep, flashcard_service: FlashcardServiceDep):
    """Get a specific flashcard deck. Requires authentication."""
    try:
        deck = flashcard_service.get_deck_by_id(deck_id, user_id)
        return DeckResponse.model_validate(deck)
    except ValidationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/decks/{deck_id}", response_model=DeckResponse)
def update_deck(
    deck_id: int,
    deck_data: DeckUpdate,
    user_id: UserIdDep,
    flashcard_service: FlashcardServiceDep,
):
    """Update a flashcard deck. Requires authentication."""
    try:
        deck = flashcard_service.update_deck(deck_id, deck_data, user_id)
        return DeckResponse.model_validate(deck)
    except ValidationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/decks/{deck_id}", status_code=204)
def delete_deck(deck_id: int, user_id: UserIdDep, flashcard_service: FlashcardServiceDep):
    """Delete a flashcard deck and all its cards. Requires authentication."""
    try:
        flashcard_service.delete_deck(deck_id, user_id)
    except ValidationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


# === Flashcard Endpoints (Nested Routes) ===


@router.post(
    "/decks/{deck_id}/cards", response_model=FlashcardResponse, status_code=201
)
def create_flashcard(
    deck_id: int,
    flashcard_data: FlashcardCreateNested,
    user_id: UserIdDep,
    flashcard_service: FlashcardServiceDep,
):
    """
    Create a new flashcard in a deck. Requires authentication.

    The flashcard will be initialized with FSRS default values for optimal spaced repetition.
    """
    try:
        flashcard = flashcard_service.create_flashcard(deck_id, flashcard_data, user_id)
        return FlashcardResponse.model_validate(flashcard)
    except ValidationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decks/{deck_id}/cards", response_model=FlashcardListResponse)
def get_flashcards(
    deck_id: int,
    user_id: UserIdDep,
    flashcard_service: FlashcardServiceDep,
    page: int = 1,
    page_size: int = 50,
):
    """Get all flashcards in a deck. Requires authentication."""
    try:
        return flashcard_service.get_flashcards(deck_id, user_id, page, page_size)
    except ValidationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decks/{deck_id}/cards/{card_id}", response_model=FlashcardResponse)
def get_flashcard(
    deck_id: int, card_id: int, user_id: UserIdDep, flashcard_service: FlashcardServiceDep
):
    """Get a specific flashcard. Requires authentication."""
    try:
        flashcard = flashcard_service.get_flashcard_by_id(deck_id, card_id, user_id)
        return FlashcardResponse.model_validate(flashcard)
    except ValidationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/decks/{deck_id}/cards/{card_id}", response_model=FlashcardResponse)
def update_flashcard(
    deck_id: int,
    card_id: int,
    flashcard_data: FlashcardUpdate,
    user_id: UserIdDep,
    flashcard_service: FlashcardServiceDep,
):
    """Update a flashcard. Requires authentication."""
    try:
        flashcard = flashcard_service.update_flashcard(
            deck_id, card_id, flashcard_data, user_id
        )
        return FlashcardResponse.model_validate(flashcard)
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
        flashcard_service.delete_flashcard(deck_id, card_id, user_id)
    except ValidationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


# === FSRS Review Endpoints ===


@router.post(
    "/decks/{deck_id}/cards/{card_id}/review",
    response_model=FlashcardReviewResponse,
    summary="Review a flashcard",
    description=(
        "Review a flashcard and update its schedule using FSRS algorithm.\n\n"
        "**Ratings:**\n"
        "- 1 = Again (forgot completely)\n"
        "- 2 = Hard (remembered with difficulty)\n"
        "- 3 = Good (remembered correctly)\n"
        "- 4 = Easy (remembered very easily)\n\n"
        "**Requires authentication**"
    ),
)
def review_flashcard(
    deck_id: int,
    card_id: int,
    review_data: FlashcardReviewRequest,
    user_id: UserIdDep,
    flashcard_service: FlashcardServiceDep,
) -> FlashcardReviewResponse:
    """Review a flashcard and update its schedule using FSRS."""
    try:
        return flashcard_service.review_flashcard(deck_id, card_id, review_data, user_id)
    except ValidationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/due",
    response_model=list[FlashcardResponse],
    summary="Get due flashcards",
    description="Get all flashcards that are due for review now. Optionally filter by deck.",
)
def get_due_flashcards(
    user_id: UserIdDep,
    flashcard_service: FlashcardServiceDep,
    deck_id: int | None = None,
    limit: int = 20,
) -> list[FlashcardResponse]:
    """Get flashcards due for review."""
    try:
        flashcards = flashcard_service.get_due_flashcards(user_id, deck_id, limit)
        return [FlashcardResponse.model_validate(fc) for fc in flashcards]
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))