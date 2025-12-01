"""Flashcard endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from ....api.deps import get_session
from ....services.flashcard_service import FlashcardService
from ....schemas.flashcard_schemas import (
    FlashcardCreate,
    FlashcardCreateNested,
    FlashcardUpdate,
    FlashcardResponse,
    DeckCreate,
    DeckUpdate,
    DeckResponse,
    FlashcardListResponse,
    DeckListResponse
)
from ....core.exceptions import ValidationException, DatabaseException

router = APIRouter(prefix="/flashcard", tags=["Flashcard"])


def get_user_id() -> str:
    """Get current user ID. TODO: Implement real authentication."""
    return "demo_user"


def get_flashcard_service(session: Session = Depends(get_session)) -> FlashcardService:
    """Get flashcard service instance."""
    return FlashcardService(session)


# ===== Deck Endpoints =====

@router.get("/decks", response_model=DeckListResponse)
def list_flashcard_decks(
    user_id: str = Depends(get_user_id),
    flashcard_service: FlashcardService = Depends(get_flashcard_service)
) -> DeckListResponse:
    """Get all decks for current user."""
    try:
        return flashcard_service.get_user_decks(user_id)
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decks", response_model=DeckResponse, status_code=201)
def create_flashcard_deck(
    deck: DeckCreate,
    user_id: str = Depends(get_user_id),
    flashcard_service: FlashcardService = Depends(get_flashcard_service)
) -> DeckResponse:
    """Create a new flashcard deck."""
    try:
        return flashcard_service.create_deck(user_id, deck)
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decks/{deck_id}", response_model=DeckResponse)
def get_flashcard_deck(
    deck_id: int,
    user_id: str = Depends(get_user_id),
    flashcard_service: FlashcardService = Depends(get_flashcard_service)
) -> DeckResponse:
    """Get a specific deck."""
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
    user_id: str = Depends(get_user_id),
    flashcard_service: FlashcardService = Depends(get_flashcard_service)
) -> DeckResponse:
    """Update a flashcard deck."""
    try:
        return flashcard_service.update_deck(deck_id, user_id, deck_update)
    except ValidationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/decks/{deck_id}", status_code=204)
def delete_flashcard_deck(
    deck_id: int,
    user_id: str = Depends(get_user_id),
    flashcard_service: FlashcardService = Depends(get_flashcard_service)
):
    """Delete a flashcard deck and all its cards."""
    try:
        flashcard_service.delete_deck(deck_id, user_id)
    except ValidationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Flashcard Endpoints (Nested under Decks) =====

@router.get("/decks/{deck_id}/cards", response_model=FlashcardListResponse)
def get_flashcards(
    deck_id: int,
    user_id: str = Depends(get_user_id),
    flashcard_service: FlashcardService = Depends(get_flashcard_service)
) -> FlashcardListResponse:
    """Get all flashcards in a deck."""
    try:
        return flashcard_service.get_deck_flashcards(deck_id, user_id)
    except ValidationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decks/{deck_id}/cards", response_model=FlashcardResponse, status_code=201)
def add_flashcard(
    deck_id: int,
    flashcard: FlashcardCreateNested,  # ✅ Sử dụng schema mới (không có deck_id)
    user_id: str = Depends(get_user_id),
    flashcard_service: FlashcardService = Depends(get_flashcard_service)
) -> FlashcardResponse:
    """Add a new flashcard to a deck."""
    try:
        # ✅ Tạo FlashcardCreate object với deck_id từ URL
        flashcard_with_deck = FlashcardCreate(
            deck_id=deck_id,
            front=flashcard.front,
            back=flashcard.back
        )
        return flashcard_service.create_flashcard(user_id, flashcard_with_deck)
    except ValidationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decks/{deck_id}/cards/{card_id}", response_model=FlashcardResponse)
def get_flashcard(
    deck_id: int,
    card_id: int,
    user_id: str = Depends(get_user_id),
    flashcard_service: FlashcardService = Depends(get_flashcard_service)
) -> FlashcardResponse:
    """Get a specific flashcard."""
    try:
        flashcard = flashcard_service.get_flashcard(card_id, user_id)
        
        # Verify card belongs to the specified deck
        if flashcard.deck_id != deck_id:
            raise HTTPException(
                status_code=404,
                detail=f"Flashcard {card_id} not found in deck {deck_id}"
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
    user_id: str = Depends(get_user_id),
    flashcard_service: FlashcardService = Depends(get_flashcard_service)
) -> FlashcardResponse:
    """Update a flashcard."""
    try:
        # Get flashcard and verify it belongs to the deck
        flashcard = flashcard_service.get_flashcard(card_id, user_id)
        
        if flashcard.deck_id != deck_id:
            raise HTTPException(
                status_code=404,
                detail=f"Flashcard {card_id} not found in deck {deck_id}"
            )
        
        return flashcard_service.update_flashcard(card_id, user_id, flashcard_update)
    except ValidationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/decks/{deck_id}/cards/{card_id}", status_code=204)
def delete_flashcard(
    deck_id: int,
    card_id: int,
    user_id: str = Depends(get_user_id),
    flashcard_service: FlashcardService = Depends(get_flashcard_service)
):
    """Delete a flashcard."""
    try:
        # Get flashcard and verify it belongs to the deck
        flashcard = flashcard_service.get_flashcard(card_id, user_id)
        
        if flashcard.deck_id != deck_id:
            raise HTTPException(
                status_code=404,
                detail=f"Flashcard {card_id} not found in deck {deck_id}"
            )
        
        flashcard_service.delete_flashcard(card_id, user_id)
    except ValidationException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))