"""Database configuration and initialization."""

from sqlmodel import SQLModel, create_engine

from ..core.config import settings
from ..utils.logging import logger


def create_database_engine():
    """Create database engine based on configuration."""
    try:
        engine = create_engine(
            settings.database_url,
            echo=settings.debug,
            pool_pre_ping=True
        )
        logger.info(f"Database engine created for: {settings.database_url}")
        return engine
    except Exception as e:
        logger.error(f"Failed to create database engine: {e}")
        raise


# Global engine instance
engine = create_database_engine()


def init_db():
    """Initialize database tables."""
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise