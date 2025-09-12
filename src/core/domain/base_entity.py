from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from core.domain.domain_event import DomainEvent


@dataclass
class BaseEntity(ABC):
    """Base class for all domain entities"""

    id: UUID
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    _domain_events: list[DomainEvent] = field(default_factory=list, init=False, repr=False)

    @abstractmethod
    def validate(self) -> None:
        """Validates that all business invariants of the entity are respected"""
        self._ensure_entity_has_valid_identity()
        self._ensure_entity_has_valid_lifecycle()

    def _ensure_entity_has_valid_identity(self) -> None:
        """An entity must have a valid identity"""
        if not self.id:
            raise ValueError("An entity must have a unique identifier")

    def _ensure_entity_has_valid_lifecycle(self) -> None:
        """An entity must respect a coherent lifecycle"""
        if not self.created_at:
            raise ValueError("An entity must have a defined creation date")

        if not self.updated_at:
            raise ValueError("An entity must have a last modification date")

        if self.updated_at < self.created_at:
            raise ValueError("An entity cannot be modified before its creation")

    def update_timestamp(self) -> None:
        """Updates the modification timestamp"""
        self.updated_at = datetime.now()

    def add_domain_event(self, event: DomainEvent) -> None:
        """Adds a domain event to the entity"""
        self._domain_events.append(event)

    def get_domain_events(self) -> tuple[DomainEvent]:
        """Returns all domain events for this entity"""
        return tuple(self._domain_events)

    def clear_domain_events(self) -> None:
        """Clears all domain events from the entity"""
        self._domain_events.clear()

    def _record_event(self, event: DomainEvent) -> None:
        """Adds a domain event to the entity."""
        self._domain_events.append(event)
