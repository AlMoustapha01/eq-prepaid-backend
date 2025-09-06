"""Database configuration for async PostgreSQL connections."""

from typing import Any

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from core.settings import get_settings


class DatabaseConfig:
    """Database configuration class for async PostgreSQL connections."""

    def __init__(self) -> None:
        """Initialize database configuration with settings."""
        self.settings = get_settings()
        self._engine_kwargs = self._get_engine_kwargs()

    def _get_engine_kwargs(self) -> dict[str, Any]:
        """Get SQLAlchemy engine configuration."""
        return {
            "echo": self.settings.app.debug,
            "echo_pool": self.settings.app.debug,
            "pool_pre_ping": True,
            "pool_recycle": 3600,  # 1 hour
            "poolclass": NullPool if self.settings.app.debug else None,
            "connect_args": {
                "server_settings": {
                    "application_name": self.settings.app.app_name,
                }
            },
        }

    def create_engine(self):
        """Create async SQLAlchemy engine."""
        return create_async_engine(self.settings.postgres.async_database_url, **self._engine_kwargs)

    @property
    def database_url(self) -> str:
        """Get async database URL."""
        return self.settings.postgres.async_database_url

    @property
    def sync_database_url(self) -> str:
        """Get sync database URL for migrations."""
        return self.settings.postgres.database_url
