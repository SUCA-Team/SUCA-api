from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
from contextlib import asynccontextmanager
from .db.db import init_db
from .api.v1.router import app as api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event
    print("Starting up...")
    init_db()
    try:
        yield
    finally:
        print("Shutting down...")

app = FastAPI(title="SUCA API", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "https://akichiro.github.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


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