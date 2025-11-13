"""Health check endpoints."""

import time
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlmodel import Session

from ....api.deps import get_session
from ....schemas.health import HealthResponse, HealthStatus
from ....core.config import settings

router = APIRouter(prefix="/health", tags=["Health"])

# Track application start time
_start_time = time.time()


@router.get("", response_model=HealthResponse)
async def health_check(session: Session = Depends(get_session)) -> HealthResponse:
    """Comprehensive health check endpoint."""
    
    # Check database connectivity
    try:
        # Simple query to test database connection
        session.connection()
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    # Calculate uptime
    uptime = time.time() - _start_time
    
    health_status = HealthStatus(
        status="healthy" if db_status == "healthy" else "degraded",
        timestamp=datetime.now().isoformat(),
        version=settings.api_version,
        database_status=db_status,
        uptime=uptime
    )
    
    return HealthResponse(
        data=health_status,
        message=f"API is {health_status.status}"
    )
