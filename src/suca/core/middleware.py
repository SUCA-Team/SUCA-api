"""Exception handling middleware and handlers."""

from typing import Union
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..core.exceptions import SUCAException
from ..schemas.base import ErrorResponse
from ..utils.logging import logger


async def suca_exception_handler(request: Request, exc: SUCAException) -> JSONResponse:
    """Handle custom SUCA exceptions."""
    logger.warning(f"SUCA Exception: {exc.message} - Details: {exc.details}")
    
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            message=exc.message,
            error_code=exc.__class__.__name__,
            details=exc.details
        ).model_dump()
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            message=exc.detail,
            error_code="HTTP_ERROR"
        ).model_dump()
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation errors."""
    logger.warning(f"Validation error: {exc.errors()}")
    
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            message="Validation error",
            error_code="VALIDATION_ERROR",
            details={"errors": exc.errors()}
        ).model_dump()
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            message="Internal server error",
            error_code="INTERNAL_ERROR"
        ).model_dump()
    )
