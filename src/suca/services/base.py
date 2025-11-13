"""Base service class with common functionality."""

from abc import ABC
from sqlmodel import Session
from typing import Type, TypeVar, Generic, Optional, List
from ..core.exceptions import DatabaseException

T = TypeVar("T")


class BaseService(ABC, Generic[T]):
    """Base service class with common CRUD operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def _handle_db_error(self, error: Exception, operation: str) -> None:
        """Handle database errors consistently."""
        raise DatabaseException(
            message=f"Database error during {operation}",
            details={"original_error": str(error)}
        )
