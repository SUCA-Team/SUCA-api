"""Health check schemas."""

from pydantic import BaseModel

from .base import BaseResponse


class HealthStatus(BaseModel):
    """Health status information."""

    status: str
    timestamp: str
    version: str
    database_status: str
    uptime: float


class HealthResponse(BaseResponse):
    """Health check response."""

    data: HealthStatus
