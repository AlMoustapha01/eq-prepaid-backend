"""Application startup and shutdown events."""

import logging
from collections.abc import Callable

logger = logging.getLogger(__name__)


def create_startup_handler() -> Callable:
    """Create application startup handler."""

    async def startup_event() -> None:
        """Handle application startup."""
        logger.info("Starting EQ Prepaid Backend API...")
        # Add any startup logic here (database connections, cache initialization, etc.)
        logger.info("EQ Prepaid Backend API started successfully")

    return startup_event


def create_shutdown_handler() -> Callable:
    """Create application shutdown handler."""

    async def shutdown_event() -> None:
        """Handle application shutdown."""
        logger.info("Shutting down EQ Prepaid Backend API...")
        # Add any cleanup logic here (close database connections, etc.)
        logger.info("EQ Prepaid Backend API shutdown complete")

    return shutdown_event
