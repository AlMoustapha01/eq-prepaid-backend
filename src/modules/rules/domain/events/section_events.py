from dataclasses import dataclass
from typing import Any

from core.domain.domain_event import DomainEvent
from modules.rules.domain.value_objects.slug import SlugValueObject


@dataclass
class SectionCreated(DomainEvent):
    """Event raised when a section is created"""

    name: str = ""
    slug: SlugValueObject = None
    description: str = ""

    def get_event_type(self) -> str:
        return "section.created"

    def _get_event_data(self) -> dict[str, Any]:
        return {"name": self.name, "slug": str(self.slug), "description": self.description}


@dataclass
class SectionActivated(DomainEvent):
    """Event raised when a section is activated"""

    def get_event_type(self) -> str:
        return "section.activated"

    def _get_event_data(self) -> dict[str, Any]:
        return {}


@dataclass
class SectionDeactivated(DomainEvent):
    """Event raised when a section is deactivated"""

    def get_event_type(self) -> str:
        return "section.deactivated"

    def _get_event_data(self) -> dict[str, Any]:
        return {}


@dataclass
class SectionNameUpdated(DomainEvent):
    """Event raised when a section name is updated"""

    old_name: str = ""
    new_name: str = ""
    old_slug: SlugValueObject = None
    new_slug: SlugValueObject = None

    def get_event_type(self) -> str:
        return "section.name_updated"

    def _get_event_data(self) -> dict[str, Any]:
        return {
            "old_name": self.old_name,
            "new_name": self.new_name,
            "old_slug": str(self.old_slug),
            "new_slug": str(self.new_slug),
        }


@dataclass
class SectionDescriptionUpdated(DomainEvent):
    """Event raised when a section description is updated"""

    old_description: str = ""
    new_description: str = ""

    def get_event_type(self) -> str:
        return "section.description_updated"

    def _get_event_data(self) -> dict[str, Any]:
        return {"old_description": self.old_description, "new_description": self.new_description}
