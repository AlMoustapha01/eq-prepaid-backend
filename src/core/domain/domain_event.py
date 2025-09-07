from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4


@dataclass
class DomainEvent(ABC):
    """Base class for all domain events"""

    aggregate_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=datetime.now)
    event_version: int = 1

    @abstractmethod
    def get_event_type(self) -> str:
        """Returns the event type identifier"""

    def to_dict(self) -> dict[str, Any]:
        """Converts the event to a dictionary representation"""
        return {
            "event_type": self.get_event_type(),
            "aggregate_id": str(self.aggregate_id),
            "occurred_at": self.occurred_at.isoformat(),
            "event_version": self.event_version,
            "data": self._get_event_data(),
        }

    @abstractmethod
    def _get_event_data(self) -> dict[str, Any]:
        """Returns the event-specific data"""
