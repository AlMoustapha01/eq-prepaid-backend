"""
Configuration settings améliorée avec support du logging.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggingSettings(BaseSettings):
    """Logging system configuration."""

    # Log level
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")

    # Log files
    file_path: str = Field(default="logs/app.log")
    max_file_size_mb: int = Field(default=100, description="Maximum file size in MB")
    backup_count: int = Field(default=10, description="Number of backup files")

    # Rotation
    rotate_by_time: bool = Field(default=False, description="Rotation by time instead of size")
    retention_days: int = Field(default=7, description="Retention period in days")

    # Format and colors
    use_colors: bool = Field(default=True, description="Enable colors in console output")
    correlation_id_length: int = Field(default=32, description="Correlation ID length")

    # Specific loggers
    suppress_noisy_loggers: bool = Field(default=True, description="Suppress verbose loggers")

    @field_validator("max_file_size_mb")
    @classmethod
    def validate_file_size(cls, v):
        """Validate the maximum file size."""
        if v <= 0:
            raise ValueError("max_file_size_mb must be positive")
        if v > 1000:  # 1GB max
            raise ValueError("max_file_size_mb cannot exceed 1000MB")
        return v

    @field_validator("backup_count")
    @classmethod
    def validate_backup_count(cls, v):
        """Validate the number of backup files."""
        if v < 0:
            raise ValueError("backup_count must be non-negative")
        if v > 50:
            raise ValueError("backup_count cannot exceed 50")
        return v

    @field_validator("retention_days")
    @classmethod
    def validate_retention_days(cls, v):
        """Validate the retention period."""
        if v < 0:
            raise ValueError("retention_days must be non-negative")
        if v > 365:
            raise ValueError("retention_days cannot exceed 365")
        return v

    model_config = SettingsConfigDict(
        env_prefix="LOG_",
        case_sensitive=False,
        extra="allow",
    )


class PostgreSQLSettings(BaseSettings):
    """PostgreSQL database configuration settings."""

    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    user: str = Field(default="eq_prepaid_user")
    password: str = Field(default="eq_prepaid_password_123")
    database: str = Field(default="eq_prepaid_db")

    @property
    def database_url(self) -> str:
        """Generate PostgreSQL connection URL."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def async_database_url(self) -> str:
        """Generate PostgreSQL async connection URL."""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @field_validator("port")
    @classmethod
    def validate_port(cls, v):
        """Validate PostgreSQL port range."""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    model_config = SettingsConfigDict(
        env_prefix="POSTGRES_",
        case_sensitive=False,
        extra="allow",
    )


class RedisSettings(BaseSettings):
    """Redis cache configuration settings."""

    host: str = Field(default="localhost")
    port: int = Field(default=6379)
    password: str | None = Field(default=None)
    db: int = Field(default=0)

    @property
    def redis_url(self) -> str:
        """Generate Redis connection URL."""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"

    @field_validator("port")
    @classmethod
    def validate_port(cls, v):
        """Validate Redis port range."""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    @field_validator("db")
    @classmethod
    def validate_db(cls, v):
        """Validate Redis database number."""
        if not 0 <= v <= 15:
            raise ValueError("Redis database must be between 0 and 15")
        return v

    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        case_sensitive=False,
        extra="allow",
    )


class AppSettings(BaseSettings):
    """Main application configuration settings."""

    app_name: str = Field(default="EQ Prepaid Backend")
    project_description: str = Field(
        default="Backend API for EQ Prepaid system with rules management"
    )
    debug: bool = Field(default=False)
    version: str = Field(default="1.0.0")
    host: str = Field(default="0.0.0.0")  # nosec B104
    port: int = Field(default=8000)

    # API Configuration
    api_v1_prefix: str = Field(default="/api/v1")
    root_path: str = Field(default="")

    # Contact Information
    contact_name: str = Field(default="EQ Prepaid Team")
    contact_email: str = Field(default="support@eqprepaid.com")

    # Security Settings
    allowed_hosts: list[str] = Field(
        default=[
            "localhost",
            "127.0.0.1",
            "*.localhost",
            "*.eqprepaid.com",  # Replace with your actual domain
        ],
    )

    backend_cors_origins: list[str] = Field(
        default=[
            "http://localhost:3000",  # React dev server
            "http://localhost:8080",  # Vue dev server
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080",
            "https://localhost:3000",
            "https://localhost:8080",
        ],
    )

    @field_validator("port")
    @classmethod
    def validate_port(cls, v):
        """Validate app port range."""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        """Parse CORS origins from environment variable or use defaults."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        if isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def assemble_allowed_hosts(cls, v):
        """Parse allowed hosts from environment variable or use defaults."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        if isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        case_sensitive=False,
        extra="allow",
    )


class Settings(BaseSettings):
    """Main settings class combining all service configurations."""

    # Service configurations
    postgres: PostgreSQLSettings = PostgreSQLSettings()
    redis: RedisSettings = RedisSettings()
    app: AppSettings = AppSettings()
    logging: LoggingSettings = LoggingSettings()

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="allow"
    )


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to ensure settings are loaded only once
    and reused throughout the application lifecycle.

    Returns:
        Settings: Configured settings instance

    """
    return Settings()


# Global settings instance
settings = get_settings()
