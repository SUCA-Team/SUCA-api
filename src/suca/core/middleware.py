"""Exception handling middleware and handlers."""

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ..core.exceptions import SUCAException
from ..utils.logging import logger


async def suca_exception_handler(request: Request, exc: SUCAException) -> JSONResponse:
    """Handle custom SUCA exceptions."""
    logger.warning(f"SUCA Exception: {exc.message} - Details: {exc.details}")

    return JSONResponse(
        status_code=400,
        content={
            "detail": exc.message,
            "success": False,
            "error_code": exc.__class__.__name__,
            "details": exc.details,
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "success": False, "error_code": "HTTP_ERROR"},
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation errors."""
    logger.warning(f"Validation error: {exc.errors()}")

    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "success": False, "error_code": "VALIDATION_ERROR"},
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "success": False,
            "error_code": "INTERNAL_ERROR",
        },
    )
