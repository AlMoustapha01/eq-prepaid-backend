"""Database lifecycle management utilities."""

import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from .connection import close_database_manager, get_database_manager
from .session import get_session_factory

logger = logging.getLogger(__name__)


async def initialize_database() -> None:
    """
    Initialize database connections and session factory.

    This function should be called during application startup.
    """
    try:
        logger.info("Initializing database connections...")

        # Initialize database manager
        db_manager = await get_database_manager()
        logger.info("Database manager initialized")

        # Initialize session factory
        await get_session_factory()
        logger.info("Session factory initialized")

        # Perform health check
        if await db_manager.health_check():
            logger.info("Database initialization completed successfully")
        else:
            raise RuntimeError("Database health check failed")

    except Exception as e:
        logger.exception(f"Database initialization failed: {e}")
        raise


async def shutdown_database() -> None:
    """
    Shutdown database connections.

    This function should be called during application shutdown.
    """
    try:
        logger.info("Shutting down database connections...")
        await close_database_manager()
        logger.info("Database shutdown completed successfully")

    except Exception as e:
        logger.exception(f"Database shutdown failed: {e}")
        raise


@asynccontextmanager
async def database_lifespan() -> AsyncGenerator[None, None]:
    """
    Database lifespan context manager for FastAPI applications.

    Usage:
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            async with database_lifespan():
                yield
    """
    try:
        await initialize_database()
        yield
    finally:
        await shutdown_database()


async def wait_for_database(max_retries: int = 30, retry_interval: float = 1.0) -> None:
    """
    Wait for database to become available.

    Args:
        max_retries: Maximum number of connection attempts
        retry_interval: Time to wait between retries in seconds

    Raises:
        RuntimeError: If database is not available after max_retries

    """
    for attempt in range(max_retries):
        try:
            db_manager = await get_database_manager()
            if await db_manager.health_check():
                logger.info(f"Database is available (attempt {attempt + 1})")
                return
        except Exception as e:
            logger.warning(f"Database not available (attempt {attempt + 1}/{max_retries}): {e}")

        if attempt < max_retries - 1:
            await asyncio.sleep(retry_interval)

    msg = f"Database not available after {max_retries} attempts"
    raise RuntimeError(msg)


async def check_database_health() -> dict:
    """
    Check database health and return status information.

    Returns:
        dict: Health status information

    """
    try:
        db_manager = await get_database_manager()
        is_healthy = await db_manager.health_check()

        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "connected": db_manager.is_connected,
            "database_url": db_manager._config.database_url.split("@")[-1],  # Hide credentials
        }
    except Exception as e:
        return {
            "status": "error",
            "connected": False,
            "error": str(e),
        }
