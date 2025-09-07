"""Database lifecycle management."""

import asyncio
import logging

from core.db.connection import get_database_manager
from core.db.session import get_session_factory


def _raise_health_check_error() -> None:
    """Raise health check error."""
    raise RuntimeError("Database health check failed")


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
            _raise_health_check_error()

    except Exception:
        logger.exception("Database initialization failed")
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

    except Exception:
        logger.exception("Database shutdown failed")
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
                logger.info("Database is available (attempt %s)", attempt + 1)
                return
        except Exception as e:
            logger.warning(
                "Database not available (attempt %s/%s): %s", attempt + 1, max_retries, e
            )

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
            "database_url": db_manager.config.database_url.split("@")[-1],  # Hide credentials
        }
    except Exception as e:
        return {
            "status": "error",
            "connected": False,
            "error": str(e),
        }
