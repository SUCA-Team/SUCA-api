"""Authentication utilities with Firebase integration."""

from datetime import UTC, datetime, timedelta

import firebase_admin
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials
from jose import JWTError, jwt
from passlib.context import CryptContext

from ..utils.logging import logger
from .config import settings

# Password hashing (for backward compatibility or custom auth)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings (for custom tokens if needed)
SECRET_KEY = settings.jwt_secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Bearer token scheme
security = HTTPBearer()

# Initialize Firebase Admin SDK
_firebase_app = None


def initialize_firebase():
    """Initialize Firebase Admin SDK."""
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app

    try:
        # Check if app is already initialized
        _firebase_app = firebase_admin.get_app()
        logger.info("Firebase Admin SDK already initialized")
    except ValueError:
        # Initialize with credentials
        try:
            cred = credentials.Certificate(settings.firebase_credentials_path)
            _firebase_app = firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
            logger.warning("Firebase authentication will not be available")
            _firebase_app = None

    return _firebase_app


# Initialize Firebase on module load
initialize_firebase()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


def verify_firebase_token(token: str) -> dict:
    """
    Verify Firebase ID token and return decoded token.

    Args:
        token: Firebase ID token from client

    Returns:
        Decoded token containing user info (uid, email, etc.)

    Raises:
        HTTPException: If token is invalid or Firebase is not initialized
    """
    if _firebase_app is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Firebase authentication is not available",
        )

    try:
        decoded_token = firebase_auth.verify_id_token(token)
        logger.debug(f"Firebase token verified for user: {decoded_token.get('uid')}")
        return decoded_token
    except firebase_auth.InvalidIdTokenError as e:
        logger.warning(f"Invalid Firebase token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except Exception as e:
        logger.error(f"Error verifying Firebase token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Dependency to get current user ID from Firebase token.

    This function verifies the Firebase ID token and returns the user's UID.

    Usage:
        @router.get("/protected")
        def protected_route(user_id: str = Depends(get_current_user_id)):
            return {"user_id": user_id}
    """
    token = credentials.credentials

    # Try Firebase token verification first
    try:
        decoded_token = verify_firebase_token(token)
        user_id = decoded_token.get("uid")
        if user_id:
            return user_id
    except HTTPException:
        # If Firebase fails, fall back to custom JWT (for backward compatibility)
        logger.debug("Firebase verification failed, trying custom JWT")
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id:
            return user_id

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Dependency to get current user info from Firebase token.

    Returns full decoded token with user information.

    Usage:
        @router.get("/protected")
        def protected_route(user: dict = Depends(get_current_user)):
            return {"user_email": user.get("email")}
    """
    token = credentials.credentials

    # Try Firebase token verification
    try:
        decoded_token = verify_firebase_token(token)
        return decoded_token
    except HTTPException:
        # Fall back to custom JWT
        logger.debug("Firebase verification failed, trying custom JWT")
        payload = decode_access_token(token)
        return payload


async def get_optional_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str | None:
    """
    Dependency to optionally get user ID (for endpoints that work with/without auth).
    """
    if not credentials:
        return None

    try:
        return await get_current_user_id(credentials)
    except HTTPException:
        return None
