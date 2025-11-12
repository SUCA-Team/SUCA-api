import json
from fastapi import APIRouter, Depends
from sqlmodel import Session, select, SQLModel
from suca.api.deps import get_session
from src.suca.schemas.flashcard_schemas import *

router = APIRouter(prefix="/flashcard", tags=["Flashcard"])

@router.get("/list_decks")
def list_flashcard_decks(session: Session = get_session()):
    pass

@router.post("/create_deck")
def create_flashcard_deck(user_id: str = Depends(get_user_id), deck: DeckCreate, session: Session = get_session()):
    pass

@router.post("/add_card")
def add_flashcard(flashcard: FlashcardCreate, session: Session = get_session()):
    pass

@router.get("/get_cards")
def get_flashcards(deck_id: str, session: Session = get_session()):
    pass

@router.delete("/delete_card")
def delete_flashcard(card_id: str, session: Session = get_session()):
    pass

@router.delete("/delete_deck")
def delete_flashcard_deck(deck_id: str, session: Session = get_session()):
    pass

@router.put("/update_card")
def update_flashcard(card_id: str, front: str | None = None, back: str | None = None, session: Session = get_session()):
    pass

@router.put("/update_deck")
def update_flashcard_deck(deck_id: str, deck_name: str, session: Session = get_session()):
    pass
