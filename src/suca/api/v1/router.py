from fastapi import APIRouter

from .endpoints import auth, flashcard, health, search

app = APIRouter(prefix="/api/v1", tags=["SUCA API v1"])

app.include_router(auth.router)
app.include_router(health.router)
app.include_router(search.router)
app.include_router(flashcard.router)
# app.include_router(translate.router)
