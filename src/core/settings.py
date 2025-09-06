"""
Configuration settings for the EQ Prepaid Backend application.
Uses Pydantic for environment variable validation and type checking.
"""

from functools import lru_cache

from pydantic import BaseSettings, Field, validator


class PostgreSQLSettings(BaseSettings):
    """PostgreSQL database configuration settings."""

    host: str = Field(default="localhost", env="POSTGRES_HOST")
    port: int = Field(default=5432, env="POSTGRES_PORT")
    user: str = Field(..., env="POSTGRES_USER")
    password: str = Field(..., env="POSTGRES_PASSWORD")
    database: str = Field(..., env="POSTGRES_DB")

    @property
    def database_url(self) -> str:
        """Generate PostgreSQL connection URL."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @classmethod
    @validator("port")
    def validate_port(cls, v):
        """Validate PostgreSQL port range."""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    class Config:
        env_prefix = "POSTGRES_"
        case_sensitive = False


class RedisSettings(BaseSettings):
    """Redis cache configuration settings."""

    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    password: str | None = Field(default=None, env="REDIS_PASSWORD")
    db: int = Field(default=0, env="REDIS_DB")

    @property
    def redis_url(self) -> str:
        """Generate Redis connection URL."""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"

    @classmethod
    @validator("port")
    def validate_port(cls, v):
        """Validate Redis port range."""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    @classmethod
    @validator("db")
    def validate_db(cls, v):
        """Validate Redis database number."""
        if not 0 <= v <= 15:
            raise ValueError("Redis database must be between 0 and 15")
        return v

    class Config:
        env_prefix = "REDIS_"
        case_sensitive = False


class AppSettings(BaseSettings):
    """Main application configuration settings."""

    app_name: str = Field(default="EQ Prepaid Backend", env="APP_NAME")
    debug: bool = Field(default=False, env="DEBUG")
    version: str = Field(default="1.0.0", env="APP_VERSION")
    host: str = Field(default="0.0.0.0", env="APP_HOST")  # nosec B104
    port: int = Field(default=8000, env="APP_PORT")

    @classmethod
    @validator("port")
    def validate_port(cls, v):
        """Validate application port range."""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    class Config:
        env_prefix = "APP_"
        case_sensitive = False


class Settings(BaseSettings):
    """Main settings class combining all service configurations."""

    # Service configurations
    postgres: PostgreSQLSettings = PostgreSQLSettings()
    redis: RedisSettings = RedisSettings()
    app: AppSettings = AppSettings()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


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
