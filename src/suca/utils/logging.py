"""Logging utilities."""

import logging
import sys

from ..core.config import settings


def setup_logging(level: str | None = None) -> logging.Logger:
    """Setup application logging."""

    log_level = level or ("DEBUG" if settings.debug else "INFO")

    # Create logger
    logger = logging.getLogger("suca")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, log_level.upper()))

    # Create formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    # Add handler to logger
    if not logger.handlers:
        logger.addHandler(handler)

    return logger


# Global logger instance
logger = setup_logging()
