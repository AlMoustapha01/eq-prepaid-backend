"""Async database connection manager for PostgreSQL."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

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
                await conn.execute("SELECT 1")

            self._is_connected = True
            logger.info("Database connection established successfully")

        except SQLAlchemyError as e:
            logger.exception(f"Failed to connect to database: {e}")
            self._is_connected = False
            raise
        except Exception as e:
            logger.exception(f"Unexpected error during database connection: {e}")
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

        except Exception as e:
            logger.exception(f"Error during database disconnection: {e}")
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
            except Exception as e:
                logger.exception(f"Error in database connection context: {e}")
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
            return True
        except Exception as e:
            logger.exception(f"Database health check failed: {e}")
            return False

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


# Global database manager instance
_database_manager: DatabaseManager | None = None


async def get_database_manager() -> DatabaseManager:
    """
    Get or create global database manager instance.

    Returns:
        DatabaseManager: Global database manager instance

    """
    global _database_manager

    if _database_manager is None:
        _database_manager = DatabaseManager()
        await _database_manager.connect()

    return _database_manager


async def close_database_manager() -> None:
    """Close global database manager."""
    global _database_manager

    if _database_manager is not None:
        await _database_manager.disconnect()
        _database_manager = None
