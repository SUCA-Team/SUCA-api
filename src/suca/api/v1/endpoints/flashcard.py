"""Flashcard endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from ....api.deps import get_session
from ....core.auth import get_current_user_id
from ....core.exceptions import DatabaseException, ValidationException
from ....schemas.flashcard_schemas import (
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
def get_due_cards(
    user_id: UserIdDep, flashcard_service: FlashcardServiceDep
) -> DueCardsResponse:
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