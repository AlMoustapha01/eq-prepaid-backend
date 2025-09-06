"""Base repository port interface."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from uuid import UUID

from .pagination import PaginatedResult, PaginationParams

# Type variables for generic repository
DomainT = TypeVar("DomainT")  # Domain entity type
PersistenceT = TypeVar("PersistenceT")  # Database model type
ResponseT = TypeVar("ResponseT")  # Response DTO type
IdT = TypeVar("IdT", UUID, str, int)  # ID type


class BaseRepositoryPort(ABC, Generic[DomainT, PersistenceT, ResponseT, IdT]):
    """Base repository port interface defining CRUD operations."""

    @abstractmethod
    async def insert_one(self, entity: DomainT) -> DomainT:
        """
        Insert a single entity.

        Args:
            entity: Domain entity to insert

        Returns:
            DomainT: Inserted domain entity

        """

    @abstractmethod
    async def insert_many(self, entities: list[DomainT]) -> list[DomainT]:
        """
        Insert multiple entities.

        Args:
            entities: List of domain entities to insert

        Returns:
            List[DomainT]: List of inserted domain entities

        """

    @abstractmethod
    async def find_by_id(self, entity_id: IdT) -> DomainT | None:
        """
        Find entity by ID.

        Args:
            entity_id: Entity identifier

        Returns:
            Optional[DomainT]: Domain entity if found, None otherwise

        """

    @abstractmethod
    async def find_all_paginated(
        self, pagination: PaginationParams, filters: dict | None = None
    ) -> PaginatedResult[DomainT]:
        """
        Find all entities with pagination.

        Args:
            pagination: Pagination parameters
            filters: Optional filters to apply

        Returns:
            PaginatedResult[DomainT]: Paginated result with domain entities

        """

    @abstractmethod
    async def delete_by_id(self, entity_id: IdT) -> bool:
        """
        Delete entity by ID.

        Args:
            entity_id: Entity identifier

        Returns:
            bool: True if entity was deleted, False if not found

        """

    @abstractmethod
    async def update(self, entity: DomainT) -> DomainT | None:
        """
        Update an existing entity.

        Args:
            entity: Domain entity with updated data

        Returns:
            Optional[DomainT]: Updated domain entity if found, None otherwise

        """

    @abstractmethod
    async def exists_by_id(self, entity_id: IdT) -> bool:
        """
        Check if entity exists by ID.

        Args:
            entity_id: Entity identifier

        Returns:
            bool: True if entity exists, False otherwise

        """

    @abstractmethod
    async def count(self, filters: dict | None = None) -> int:
        """
        Count entities with optional filters.

        Args:
            filters: Optional filters to apply

        Returns:
            int: Number of entities matching criteria

        """
