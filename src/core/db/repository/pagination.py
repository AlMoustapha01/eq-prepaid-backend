"""Pagination utilities for repository operations."""

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class PaginationParams:
    """Parameters for pagination."""

    page: int = 1
    size: int = 10

    def __post_init__(self):
        """Validate pagination parameters."""
        if self.page < 1:
            raise ValueError("Page must be >= 1")
        if self.size < 1:
            raise ValueError("Size must be >= 1")
        if self.size > 100:
            raise ValueError("Size must be <= 100")

    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        """Get limit for database query."""
        return self.size


@dataclass
class PaginatedResult(Generic[T]):
    """Result container for paginated queries."""

    items: list[T]
    total: int
    page: int
    size: int

    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        if self.total == 0:
            return 0
        return (self.total + self.size - 1) // self.size

    @property
    def has_next(self) -> bool:
        """Check if there are more pages."""
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        """Check if there are previous pages."""
        return self.page > 1

    @property
    def next_page(self) -> int | None:
        """Get next page number."""
        return self.page + 1 if self.has_next else None

    @property
    def previous_page(self) -> int | None:
        """Get previous page number."""
        return self.page - 1 if self.has_previous else None
