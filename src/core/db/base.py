"""Base database model and utilities."""

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

from .mixins import TimestampMixin, UUIDMixin, UUIDStringMixin


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all database models."""


class UUIDTimestampMixin(UUIDMixin, TimestampMixin):
    """Mixin combining UUID primary key and timestamp fields."""


class UUIDStringTimestampMixin(UUIDStringMixin, TimestampMixin):
    """Mixin combining UUID string primary key and timestamp fields."""
