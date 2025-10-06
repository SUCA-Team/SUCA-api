from fastapi import FastAPI
from pydantic import BaseModel
from contextlib import asynccontextmanager
from .db.db import connect_db, close_db
from .api.v1.router import app as api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event
    print("Starting up...")
    await connect_db(app)
    yield
    # Shutdown event
    print("Shutting down...")
    await close_db(app)

app = FastAPI(title="SUCA API", lifespan=lifespan)


app.include_router(api_router)

# class Entry(BaseModel):
#     id: int
#     name: str
#     description: str | None = None



# @app.get("/health", tags=["Health"])
# async def health_check() -> Entry:
#     """
#     Health check endpoint to verify that the API is running.
#     """
#     return Entry(id=1, name="Health Check", description="API is healthy")

# @app.post("/items/", response_model=Entry, tags=["Items"])
# async def create_item(item: Entry) -> Entry:
#     """
#     Create a new item.
#     """
#     return item