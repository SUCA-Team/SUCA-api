"""Authentication endpoints with Firebase integration."""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from ....core.auth import (
    get_current_user,
    get_current_user_id,
    verify_firebase_token,
)
from ....utils.logging import logger

router = APIRouter(prefix="/auth", tags=["Authentication"])
limiter = Limiter(key_func=get_remote_address)


# ===== Schemas =====


class FirebaseTokenVerify(BaseModel):
    """Firebase ID token verification schema."""

    id_token: str = Field(
        ...,
        description="Firebase ID token from client SDK",
        examples=["eyJhbGciOiJSUzI1NiIsImtpZCI6IjAx..."],
    )


class UserResponse(BaseModel):
    """User info response."""

    user_id: str = Field(
        ..., 
        description="Unique user identifier (Firebase UID)", 
        examples=["firebase_uid_123"]
    )
    email: str | None = Field(
        None, 
        description="User email", 
        examples=["user@example.com"]
    )
    email_verified: bool | None = Field(
        None, 
        description="Whether email is verified"
    )
    display_name: str | None = Field(
        None, 
        description="User display name", 
        examples=["John Doe"]
    )
    photo_url: str | None = Field(
        None, 
        description="User photo URL"
    )


# ===== Endpoints =====


@router.post(
    "/verify",
    response_model=UserResponse,
    summary="Verify Firebase ID token",
    description=(
        "Verify a Firebase ID token and get user information.\n\n"
        "**Primary authentication method** - Use this endpoint to verify tokens from Firebase Client SDK.\n\n"
        "**Client-side flow:**\n"
        "1. User signs in with Firebase Auth (Google, Email, etc.)\n"
        "2. Get ID token: `user.getIdToken()`\n"
        "3. Send token to this endpoint for verification\n"
        "4. Use the verified token for subsequent API calls\n\n"
        "**Response includes:**\n"
        "- Firebase UID (user_id)\n"
        "- Email and verification status\n"
        "- Display name and photo URL"
    ),
)
@limiter.limit("30/minute")
def verify_token(request: Request, token_data: FirebaseTokenVerify) -> UserResponse:
    """
    Verify Firebase ID token and return user information.
    
    This is the primary authentication endpoint for Firebase-authenticated users.
    """
    try:
        decoded_token = verify_firebase_token(token_data.id_token)
        
        logger.info(f"Token verified for Firebase user: {decoded_token.get('uid')}")
        
        return UserResponse(
            user_id=decoded_token.get("uid", ""),
            email=decoded_token.get("email"),
            email_verified=decoded_token.get("email_verified"),
            display_name=decoded_token.get("name"),
            photo_url=decoded_token.get("picture"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from e


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user info",
    description=(
        "Get information about the currently authenticated user.\n\n"
        "**Requires:** Valid Firebase ID token in Authorization header\n\n"
        "**Example:**\n"
        "```\n"
        "Authorization: Bearer <firebase_id_token>\n"
        "```\n\n"
        "The token is verified with Firebase Auth and user info is returned."
    ),
)
async def get_me(user_data: Annotated[dict, Depends(get_current_user)]) -> UserResponse:
    """
    Get current authenticated user info from Firebase token.
    Requires valid Firebase ID token in Authorization header.
    """
    return UserResponse(
        user_id=user_data.get("uid", ""),
        email=user_data.get("email"),
        email_verified=user_data.get("email_verified"),
        display_name=user_data.get("name"),
        photo_url=user_data.get("picture"),
    )


@router.post(
    "/refresh",
    summary="Refresh Firebase ID token",
    description=(
        "Endpoint to trigger token refresh on the client side.\n\n"
        "**Note:** Actual token refresh happens on the client using Firebase SDK.\n"
        "This endpoint validates the current token and prompts client to refresh.\n\n"
        "**Client-side:**\n"
        "```javascript\n"
        "const user = firebase.auth().currentUser;\n"
        "const token = await user.getIdToken(true); // force refresh\n"
        "```"
    ),
)
@limiter.limit("10/minute")
async def refresh_token(request: Request, user_id: Annotated[str, Depends(get_current_user_id)]):
    """
    Validate current token and return success.
    Client should refresh token using Firebase SDK.
    """
    logger.info(f"Token refresh requested for user: {user_id}")
    return {
        "success": True,
        "message": "Token is valid. Refresh on client side using Firebase SDK.",
        "user_id": user_id,
    }
