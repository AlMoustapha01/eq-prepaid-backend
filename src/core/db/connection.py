"""Async database connection manager for PostgreSQL."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from .config import DatabaseConfig

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages async database connections and lifecycle."""

    def __init__(self) -> None:
        """Initialize database manager."""
        self._config = DatabaseConfig()
        self._engine: AsyncEngine | None = None
        self._is_connected = False

    async def connect(self) -> None:
        """Initialize database connection."""
        if self._engine is not None:
            logger.warning("Database engine already initialized")
            return

        try:
            self._engine = self._config.create_engine()

            # Test connection
            async with self._engine.begin() as conn:
                await conn.execute(text("SELECT 1"))

            self._is_connected = True
            logger.info("Database connection established successfully")

        except SQLAlchemyError:
            logger.exception("Failed to connect to database")
            self._is_connected = False
            raise
        except Exception:
            logger.exception("Unexpected error during database connection")
            self._is_connected = False
            raise

    async def disconnect(self) -> None:
        """Close database connection."""
        if self._engine is None:
            logger.warning("Database engine not initialized")
            return

        try:
            await self._engine.dispose()
            self._engine = None
            self._is_connected = False
            logger.info("Database connection closed successfully")

        except Exception:
            logger.exception("Error during database disconnection")
            raise

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[AsyncConnection, None]:
        """
        Get async database connection context manager.

        Yields:
            AsyncConnection: Database connection

        Raises:
            RuntimeError: If database is not connected

        """
        if not self.is_connected:
            raise RuntimeError("Database is not connected. Call connect() first.")

        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception:
                logger.exception("Error in database connection context")
                await connection.rollback()
                raise

    @property
    def engine(self) -> AsyncEngine:
        """Get the database engine."""
        if self._engine is None:
            raise RuntimeError("Database engine not initialized. Call connect() first.")
        return self._engine

    @property
    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self._is_connected and self._engine is not None

    async def health_check(self) -> bool:
        """
        Perform database health check.

        Returns:
            bool: True if database is healthy, False otherwise

        """
        if not self.is_connected:
            return False
        try:
            async with self.get_connection() as conn:
                await conn.execute("SELECT 1")
        except Exception:
            logger.exception("Database health check failed")
            return False
        else:
            return True

    async def execute_raw_sql(self, sql: str, parameters: dict | None = None) -> any:
        """
        Execute raw SQL query.

        Args:
            sql: SQL query string
            parameters: Query parameters

        Returns:
            Query result

        """
        if parameters is None:
            parameters = {}

        async with self.get_connection() as conn:
            return await conn.execute(sql, parameters)


class _ManagerHolder:
    instance: DatabaseManager | None = None


async def get_database_manager() -> DatabaseManager:
    """
    Get or create global database manager instance.

    Returns:
        DatabaseManager: Global database manager instance

    """
    if _ManagerHolder.instance is None:
        mgr = DatabaseManager()
        await mgr.connect()
        _ManagerHolder.instance = mgr

    return _ManagerHolder.instance


async def close_database_manager() -> None:
    """Close global database manager."""
    if _ManagerHolder.instance is not None:
        await _ManagerHolder.instance.disconnect()
        _ManagerHolder.instance = None
