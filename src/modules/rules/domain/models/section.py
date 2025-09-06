from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel

from core.domain.base_entity import BaseEntity
from modules.rules.domain.events.section_events import (
    SectionActivated,
    SectionCreated,
    SectionDeactivated,
    SectionDescriptionUpdated,
    SectionNameUpdated,
)
from modules.rules.domain.value_objects.slug import SlugValueObject


class SectionStatus(Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class CreateSectionDto(BaseModel):
    name: str
    description: str


@dataclass
class SectionEntity(BaseEntity):
    name: str = ""
    slug: SlugValueObject = None
    description: str = ""
    status: SectionStatus = None

    def validate(self) -> None:
        """Validates that all business invariants of the entity are respected"""
        super().validate()

    @classmethod
    def create(cls, dto: CreateSectionDto) -> "SectionEntity":
        entity = cls(
            id=uuid4(),
            name=dto.name,
            slug=SlugValueObject.from_name(dto.name),
            description=dto.description,
            status=SectionStatus.ACTIVE,
        )
        entity.validate()

        # Publish domain event
        event = SectionCreated(
            aggregate_id=entity.id,
            occurred_at=datetime.now(),
            name=entity.name,
            slug=entity.slug,
            description=entity.description,
        )
        entity.add_domain_event(event)

        return entity

    def make_active(self) -> None:
        if self.status != SectionStatus.ACTIVE:
            self.status = SectionStatus.ACTIVE
            self.update_timestamp()
            self.validate()

            # Publish domain event
            event = SectionActivated(aggregate_id=self.id, occurred_at=datetime.now())
            self.add_domain_event(event)

    def make_inactive(self) -> None:
        if self.status != SectionStatus.INACTIVE:
            self.status = SectionStatus.INACTIVE
            self.update_timestamp()
            self.validate()

            # Publish domain event
            event = SectionDeactivated(aggregate_id=self.id, occurred_at=datetime.now())
            self.add_domain_event(event)

    def update_name(self, name: str) -> None:
        if self.name != name:
            old_name = self.name
            old_slug = self.slug

            self.name = name
            self.slug = SlugValueObject.from_name(name)
            self.update_timestamp()
            self.validate()

            # Publish domain event
            event = SectionNameUpdated(
                aggregate_id=self.id,
                occurred_at=datetime.now(),
                old_name=old_name,
                new_name=self.name,
                old_slug=old_slug,
                new_slug=self.slug,
            )
            self.add_domain_event(event)

    def update_description(self, description: str) -> None:
        if self.description != description:
            old_description = self.description

            self.description = description
            self.update_timestamp()
            self.validate()

            # Publish domain event
            event = SectionDescriptionUpdated(
                aggregate_id=self.id,
                occurred_at=datetime.now(),
                old_description=old_description,
                new_description=self.description,
            )
            self.add_domain_event(event)
