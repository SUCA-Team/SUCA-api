"""Base schemas for common response patterns."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class BaseResponse(BaseModel):
    """Base response model."""

    success: bool = True
    message: str | None = None


class ErrorResponse(BaseResponse):
    """Error response model."""

    success: bool = False
    error_code: str | None = None
    details: dict[str, Any] | None = None


class PaginatedResponse(BaseResponse, Generic[T]):
    """Paginated response model."""

    data: list[T]
    total_count: int
    page: int = 1
    page_size: int = 10
    total_pages: int

    @classmethod
    def create(
        cls,
        data: list[T],
        total_count: int,
        page: int = 1,
        page_size: int = 10,
        message: str | None = None,
    ):
        """Create a paginated response."""
        total_pages = (total_count + page_size - 1) // page_size
        return cls(
            data=data,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            message=message,
        )
