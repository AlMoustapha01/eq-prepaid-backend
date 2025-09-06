"""Async database session factory and management."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .connection import get_database_manager

logger = logging.getLogger(__name__)


class AsyncSessionFactory:
    """Factory for creating async database sessions."""

    def __init__(self) -> None:
        """Initialize session factory."""
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    async def initialize(self) -> None:
        """Initialize the session factory with database engine."""
        if self._session_factory is not None:
            logger.warning("Session factory already initialized")
            return

        try:
            db_manager = await get_database_manager()
            self._session_factory = async_sessionmaker(
                bind=db_manager.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False,
            )
            logger.info("Session factory initialized successfully")

        except Exception as e:
            logger.exception(f"Failed to initialize session factory: {e}")
            raise

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get async database session context manager.

        Yields:
            AsyncSession: Database session

        Raises:
            RuntimeError: If session factory is not initialized

        """
        if self._session_factory is None:
            raise RuntimeError("Session factory not initialized. Call initialize() first.")

        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except SQLAlchemyError as e:
                logger.exception(f"Database error in session: {e}")
                await session.rollback()
                raise
            except Exception as e:
                logger.exception(f"Unexpected error in session: {e}")
                await session.rollback()
                raise

    def create_session(self) -> AsyncSession:
        """
        Create a new async database session.

        Returns:
            AsyncSession: New database session

        Raises:
            RuntimeError: If session factory is not initialized

        """
        if self._session_factory is None:
            raise RuntimeError("Session factory not initialized. Call initialize() first.")

        return self._session_factory()

    @property
    def is_initialized(self) -> bool:
        """Check if session factory is initialized."""
        return self._session_factory is not None


# Global session factory instance
_session_factory: AsyncSessionFactory | None = None


async def get_session_factory() -> AsyncSessionFactory:
    """
    Get or create global session factory instance.

    Returns:
        AsyncSessionFactory: Global session factory instance

    """
    global _session_factory

    if _session_factory is None:
        _session_factory = AsyncSessionFactory()
        await _session_factory.initialize()

    return _session_factory


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get async database session.

    This function is designed to be used with FastAPI's dependency injection.

    Yields:
        AsyncSession: Database session

    """
    session_factory = await get_session_factory()
    async with session_factory.get_session() as session:
        yield session


@asynccontextmanager
async def get_session_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session in a context manager.

    Yields:
        AsyncSession: Database session

    """
    session_factory = await get_session_factory()
    async with session_factory.get_session() as session:
        yield session
