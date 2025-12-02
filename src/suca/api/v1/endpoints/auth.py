"""Authentication endpoints."""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from slowapi import Limiter
from slowapi.util import get_remote_address

from ....core.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    get_current_user_id,
    get_password_hash,
    verify_password,
)
from ....utils.logging import logger

router = APIRouter(prefix="/auth", tags=["Authentication"])
limiter = Limiter(key_func=get_remote_address)


# ===== Schemas with Examples =====


class UserRegister(BaseModel):
    """User registration schema."""

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Username (3-50 characters, alphanumeric and underscores)",
        examples=["john_doe"],
    )
    email: EmailStr = Field(
        ...,
        description="Valid email address",
        examples=["john@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (8-128 characters)",
        examples=["mypassword123"],
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format."""
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        if len(v) > 50:
            raise ValueError("Username must be at most 50 characters")
        if not v.replace("_", "").isalnum():
            raise ValueError("Username must contain only letters, numbers, and underscores")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if len(v) > 128:
            raise ValueError("Password must be at most 128 characters")
        return v


class UserLogin(BaseModel):
    """User login schema."""

    username: str = Field(
        ...,
        description="Your username",
        examples=["demo_user"],  # ← Demo account example
    )
    password: str = Field(
        ...,
        description="Your password",
        examples=["password123"],  # ← Demo password example
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "username": "demo_user",
                    "password": "password123",
                }
            ]
        }
    }


class Token(BaseModel):
    """Token response schema."""

    access_token: str = Field(
        ...,
        description="JWT access token",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer')",
    )
    expires_in: int = Field(
        ...,
        description="Token expiration time in seconds",
        examples=[1800],
    )


class UserResponse(BaseModel):
    """User info response."""

    user_id: str = Field(..., description="Unique user identifier", examples=["demo_user"])
    username: str = Field(..., description="Username", examples=["demo_user"])
    email: str = Field(..., description="User email", examples=["demo@example.com"])


# ===== Mock User Database =====


def _init_mock_users():
    """Initialize mock users database."""
    return {
        "demo_user": {
            "user_id": "demo_user",
            "username": "demo_user",
            "email": "demo@example.com",
            "hashed_password": get_password_hash("password123"),
        }
    }


MOCK_USERS_DB = {}


def get_mock_users_db():
    """Get or initialize mock users database."""
    global MOCK_USERS_DB
    if not MOCK_USERS_DB:
        MOCK_USERS_DB = _init_mock_users()
    return MOCK_USERS_DB


# ===== Endpoints =====


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description=(
        "Create a new user account and receive a JWT access token.\n\n"
        "**Validation:**\n"
        "- Username: 3-50 characters, alphanumeric and underscores only\n"
        "- Password: 8-128 characters\n"
        "- Email: Valid email format\n\n"
        "**Rate limit:** 5 registrations per hour per IP"
    ),
)
@limiter.limit("5/hour")
def register(request: Request, user_data: UserRegister) -> Token:
    """Register a new user."""
    users_db = get_mock_users_db()

    if user_data.username in users_db:
        logger.warning(f"Duplicate registration attempt for username: {user_data.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered"
        )

    user_id = f"user_{len(users_db) + 1}"
    users_db[user_data.username] = {
        "user_id": user_id,
        "username": user_data.username,
        "email": user_data.email,
        "hashed_password": get_password_hash(user_data.password),
    }

    logger.info(f"New user registered: {user_data.username} (ID: {user_id})")

    access_token = create_access_token(
        data={"sub": user_id, "username": user_data.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return Token(
        access_token=access_token, token_type="bearer", expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post(
    "/login",
    response_model=Token,
    summary="Login and get access token",
    description=(
        "Login with username and password to receive a JWT access token.\n\n"
        "**Demo Account for Testing:**\n"
        "- Username: `demo_user`\n"
        "- Password: `password123`\n\n"
        "**Rate limit:** 5 login attempts per minute per IP\n\n"
        "**Token expires in:** 30 minutes"
    ),
)
@limiter.limit("5/minute")
def login(request: Request, credentials: UserLogin) -> Token:
    """Login and get access token."""
    users_db = get_mock_users_db()
    user = users_db.get(credentials.username)

    if not user or not verify_password(credentials.password, user["hashed_password"]):
        logger.warning(f"Failed login attempt for username: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"Successful login for user: {credentials.username}")

    access_token = create_access_token(
        data={"sub": user["user_id"], "username": user["username"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return Token(
        access_token=access_token, token_type="bearer", expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user info",
    description=(
        "Get information about the currently authenticated user.\n\n"
        "**Requires:** Valid JWT token in Authorization header\n\n"
        "**Example:**\n"
        "```\n"
        "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...\n"
        "```"
    ),
)
def get_current_user(user_id: Annotated[str, Depends(get_current_user_id)]) -> UserResponse:
    """
    Get current authenticated user info.
    Requires valid JWT token in Authorization header.
    """
    users_db = get_mock_users_db()

    for user in users_db.values():
        if user["user_id"] == user_id:
            return UserResponse(
                user_id=user["user_id"], username=user["username"], email=user["email"]
            )

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")