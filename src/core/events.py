"""Application startup and shutdown events améliorés."""

import logging
import os
from collections.abc import Callable
from pathlib import Path

from core.logger import cleanup_old_logs, setup_logging


def create_startup_handler() -> Callable:
    """Create application startup event handler."""

    async def startup_event() -> None:
        """Handle application startup."""
        # Configure logging une seule fois au démarrage
        setup_logging()
        logger = logging.getLogger(__name__)

        logger.info("Starting EQ Prepaid Backend API...")
        logger.info("Application version: %s", os.getenv("APP_VERSION", "unknown"))
        logger.info(
            "Environment: %s",
            "development" if os.getenv("APP_DEBUG", "false").lower() == "true" else "production",
        )

        # Add any startup logic here (database connections, cache initialization, etc.)
        try:
            # Exemple : nettoyage des anciens logs au démarrage
            log_dir = Path("logs")
            if log_dir.exists():
                deleted_count = cleanup_old_logs(log_dir, retention_days=7)
                if deleted_count > 0:
                    logger.info("Cleaned up %d old log files", deleted_count)

        except Exception as e:
            logger.warning("Failed to cleanup old logs during startup: %s", e)

        logger.info("EQ Prepaid Backend API started successfully")

    return startup_event


def create_shutdown_handler() -> Callable:
    """Create application shutdown event handler."""

    async def shutdown_event() -> None:
        """Handle application shutdown."""
        # Pas besoin de reconfigurer le logging ici
        logger = logging.getLogger(__name__)

        logger.info("Shutting down EQ Prepaid Backend API...")

        # Add any cleanup logic here (close database connections, etc.)
        try:
            # Exemple : log final des statistiques ou nettoyage
            logger.info("Performing final cleanup...")

        except Exception as e:
            logger.error("Error during shutdown cleanup: %s", e)

        logger.info("EQ Prepaid Backend API shutdown complete")

    return shutdown_event
