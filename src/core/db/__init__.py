"""Database package for async PostgreSQL connections with SQLAlchemy."""

from .base import Base, UUIDStringTimestampMixin, UUIDTimestampMixin
from .config import DatabaseConfig
from .connection import DatabaseManager, get_database_manager
from .lifecycle import (
    check_database_health,
    database_lifespan,
    initialize_database,
    shutdown_database,
    wait_for_database,
)
from .mixins import (
    TimestampMixin,
    UUIDFieldMixin,
    UUIDMixin,
    UUIDStringMixin,
)
from .repository import (
    BaseMapper,
    BaseRepository,
    BaseRepositoryPort,
    PaginatedResult,
    PaginationParams,
)
from .session import AsyncSessionFactory, get_async_session, get_session_context

__all__ = [
    # Session management
    "AsyncSessionFactory",
    # Base classes
    "Base",
    "BaseMapper",
    "BaseRepository",
    # Repository pattern
    "BaseRepositoryPort",
    # Configuration
    "DatabaseConfig",
    # Connection management
    "DatabaseManager",
    "PaginatedResult",
    "PaginationParams",
    "TimestampMixin",
    "UUIDFieldMixin",
    "UUIDMixin",
    "UUIDStringMixin",
    "UUIDStringTimestampMixin",
    "UUIDTimestampMixin",
    "check_database_health",
    "database_lifespan",
    "get_async_session",
    "get_database_manager",
    "get_session_context",
    # Lifecycle management
    "initialize_database",
    "shutdown_database",
    "wait_for_database",
]
