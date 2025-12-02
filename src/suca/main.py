"""Main FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .api.v1.router import app as api_router
from .core.config import settings
from .core.exceptions import SUCAException
from .core.middleware import (
    general_exception_handler,
    http_exception_handler,
    suca_exception_handler,
    validation_exception_handler,
)
from .core.validators import validate_jwt_secret, validate_required_env_vars
from .db.db import init_db
from .utils.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger = setup_logging()

    # Validate environment
    try:
        validate_required_env_vars()
        validate_jwt_secret()
    except ValueError as e:
        logger.error(f"Environment validation failed: {e}")
        if not settings.debug:
            raise

    # Startup event
    logger.info(f"Starting {settings.api_title} v{settings.api_version}...")
    init_db()
    logger.info("Application startup complete")

    try:
        yield
    finally:
        logger.info("Shutting down...")


# Create limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    lifespan=lifespan,
    debug=settings.debug,
    # Enhanced documentation
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "Authentication and user management endpoints. "
            "Use `/auth/login` to get a JWT token, then click the 'Authorize' button.",
        },
        {"name": "Health", "description": "Health check and system status endpoints."},
        {
            "name": "Search",
            "description": "Japanese dictionary search with intelligent prioritization.",
        },
        {
            "name": "Flashcard",
            "description": "Flashcard management for language learning. **Requires authentication.**",
        },
    ],
    # Security schemes
    swagger_ui_parameters={
        "persistAuthorization": True,  # Remember authorization across page reloads
    },
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
