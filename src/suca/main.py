"""Main FastAPI application."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager

from .core.config import settings
from .core.exceptions import SUCAException
from .core.middleware import (
    suca_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from .db.db import init_db
from .api.v1.router import app as api_router
from .utils.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Setup logging
    logger = setup_logging()
    
    # Startup event
    logger.info(f"Starting {settings.api_title} v{settings.api_version}...")
    init_db()
    logger.info("Application startup complete")
    
    try:
        yield
    finally:
        logger.info("Shutting down...")


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    lifespan=lifespan,
    debug=settings.debug
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(SUCAException, suca_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include API routes
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