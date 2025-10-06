from fastapi import APIRouter
from .endpoints import search, translate

app = APIRouter(prefix="/api/v1", tags=["SUCA API"])

app.include_router(search.router)
app.include_router(translate.router)