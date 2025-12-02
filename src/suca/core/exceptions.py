"""Custom exceptions for the SUCA API."""

from typing import Any

from fastapi import HTTPException


class SUCAException(Exception):
    """Base exception class for SUCA API."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class SearchException(SUCAException):
    """Exception raised when search operations fail."""

    pass


class TranslationException(SUCAException):
    """Exception raised when translation operations fail."""

    pass


class DatabaseException(SUCAException):
    """Exception raised when database operations fail."""

    pass


class ValidationException(SUCAException):
    """Exception raised when validation fails."""

    pass


# HTTP Exception helpers
class HTTPExceptions:
    """Common HTTP exceptions."""

    @staticmethod
    def not_found(detail: str = "Resource not found") -> HTTPException:
        return HTTPException(status_code=404, detail=detail)

    @staticmethod
    def bad_request(detail: str = "Bad request") -> HTTPException:
        return HTTPException(status_code=400, detail=detail)

    @staticmethod
    def internal_server_error(detail: str = "Internal server error") -> HTTPException:
        return HTTPException(status_code=500, detail=detail)

    @staticmethod
    def unprocessable_entity(detail: str = "Unprocessable entity") -> HTTPException:
        return HTTPException(status_code=422, detail=detail)
