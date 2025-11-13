"""Base schemas for common response patterns."""

from pydantic import BaseModel
from typing import Any, Dict, Generic, List, Optional, TypeVar

T = TypeVar("T")


class BaseResponse(BaseModel):
    """Base response model."""
    success: bool = True
    message: Optional[str] = None


class ErrorResponse(BaseResponse):
    """Error response model."""
    success: bool = False
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class PaginatedResponse(BaseResponse, Generic[T]):
    """Paginated response model."""
    data: List[T]
    total_count: int
    page: int = 1
    page_size: int = 10
    total_pages: int
    
    @classmethod
    def create(
        cls,
        data: List[T],
        total_count: int,
        page: int = 1,
        page_size: int = 10,
        message: Optional[str] = None
    ):
        """Create a paginated response."""
        total_pages = (total_count + page_size - 1) // page_size
        return cls(
            data=data,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            message=message
        )
