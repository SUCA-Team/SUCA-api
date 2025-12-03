"""Database configuration and initialization."""

from sqlalchemy.engine import Engine
from sqlmodel import SQLModel, create_engine

from ..core.config import settings
from ..utils.logging import logger

# Global engine instance (lazy initialization)
_engine: Engine | None = None


def get_engine() -> Engine:
    """Get or create database engine (singleton pattern)."""
    global _engine
    if _engine is None:
        _engine = create_database_engine()
    return _engine


def create_database_engine(database_url: str | None = None) -> Engine:
    """Create database engine based on configuration."""
    url = database_url or settings.database_url
    try:
        engine = create_engine(url, echo=settings.debug, pool_pre_ping=True)
        logger.info(f"Database engine created for: {url}")
        return engine
    except Exception as e:
        logger.error(f"Failed to create database engine: {e}")
        raise


def set_engine(engine: Engine) -> None:
    """Set custom engine (used in testing)."""
    global _engine
    _engine = engine


def init_db() -> None:
    """Initialize database tables."""
    try:
        engine = get_engine()
        SQLModel.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
