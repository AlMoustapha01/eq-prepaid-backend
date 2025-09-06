"""Base mapper class for converting between domain, persistence, and response models."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

# Type variables for mapper
DomainT = TypeVar("DomainT")  # Domain entity type
PersistenceT = TypeVar("PersistenceT")  # Database model type
ResponseT = TypeVar("ResponseT")  # Response DTO type


class BaseMapper(ABC, Generic[DomainT, PersistenceT, ResponseT]):
    """Base mapper class for model conversions."""

    @abstractmethod
    def to_domain(self, persistence_model: PersistenceT) -> DomainT:
        """
        Convert persistence model to domain entity.

        Args:
            persistence_model: Database model instance

        Returns:
            DomainT: Domain entity

        """

    @abstractmethod
    def to_persistence(self, domain_entity: DomainT) -> PersistenceT:
        """
        Convert domain entity to persistence model.

        Args:
            domain_entity: Domain entity instance

        Returns:
            PersistenceT: Database model

        """

    @abstractmethod
    def to_response(self, domain_entity: DomainT) -> ResponseT:
        """
        Convert domain entity to response DTO.

        Args:
            domain_entity: Domain entity instance

        Returns:
            ResponseT: Response DTO

        """

    def to_domain_list(self, persistence_models: list[PersistenceT]) -> list[DomainT]:
        """
        Convert list of persistence models to domain entities.

        Args:
            persistence_models: List of database model instances

        Returns:
            List[DomainT]: List of domain entities

        """
        return [self.to_domain(model) for model in persistence_models]

    def to_persistence_list(self, domain_entities: list[DomainT]) -> list[PersistenceT]:
        """
        Convert list of domain entities to persistence models.

        Args:
            domain_entities: List of domain entity instances

        Returns:
            List[PersistenceT]: List of database models

        """
        return [self.to_persistence(entity) for entity in domain_entities]

    def to_response_list(self, domain_entities: list[DomainT]) -> list[ResponseT]:
        """
        Convert list of domain entities to response DTOs.

        Args:
            domain_entities: List of domain entity instances

        Returns:
            List[ResponseT]: List of response DTOs

        """
        return [self.to_response(entity) for entity in domain_entities]

    def to_domain_optional(self, persistence_model: PersistenceT | None) -> DomainT | None:
        """
        Convert optional persistence model to optional domain entity.

        Args:
            persistence_model: Optional database model instance

        Returns:
            Optional[DomainT]: Optional domain entity

        """
        return self.to_domain(persistence_model) if persistence_model is not None else None

    def to_response_optional(self, domain_entity: DomainT | None) -> ResponseT | None:
        """
        Convert optional domain entity to optional response DTO.

        Args:
            domain_entity: Optional domain entity instance

        Returns:
            Optional[ResponseT]: Optional response DTO

        """
        return self.to_response(domain_entity) if domain_entity is not None else None
