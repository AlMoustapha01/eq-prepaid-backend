from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, field_validator

from core.domain.base_entity import BaseEntity
from modules.rules.domain.events.section_events import (
    SectionActivated,
    SectionCreated,
    SectionDeactivated,
    SectionDescriptionUpdated,
    SectionNameUpdated,
)
from modules.rules.domain.value_objects.enums import SectionStatus
from modules.rules.domain.value_objects.slug import SlugValueObject


class CreateSectionDto(BaseModel):
    name: str
    description: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Section name cannot be empty")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Section description cannot be empty")
        return v


@dataclass
class SectionEntity(BaseEntity):
    name: str = ""
    slug: SlugValueObject = None
    description: str = ""
    status: SectionStatus = None

    def validate(self) -> None:
        """Validates that all business invariants of the entity are respected"""
        super().validate()

        if not self.name.strip():
            raise ValueError("Section must have a name")

        if not self.slug:
            raise ValueError("Section must have a valid slug")

        if self.status not in SectionStatus:
            raise ValueError("Section must have a valid status")

        if self.status == SectionStatus.ACTIVE and not self.description.strip():
            raise ValueError("Active section must have a non-empty description")

    def __post_init__(self) -> None:
        self.validate()

    @classmethod
    def create(cls, dto: CreateSectionDto) -> "SectionEntity":
        entity = cls(
            id=uuid4(),
            name=dto.name,
            slug=SlugValueObject.from_name(dto.name),
            description=dto.description,
            status=SectionStatus.ACTIVE,
        )

        # Publish domain event
        entity._record_event(
            SectionCreated(
                aggregate_id=entity.id,
                occurred_at=datetime.now(),
                name=entity.name,
                slug=entity.slug,
                description=entity.description,
                status=entity.status,
            )
        )

        return entity

    def make_active(self) -> None:
        if self.status != SectionStatus.ACTIVE:
            self.status = SectionStatus.ACTIVE
            self.update_timestamp()
            self.validate()

            # Publish domain event
            self._record_event(
                SectionActivated(
                    aggregate_id=self.id,
                    occurred_at=datetime.now(),
                )
            )

    def make_inactive(self) -> None:
        if self.status != SectionStatus.INACTIVE:
            self.status = SectionStatus.INACTIVE
            self.update_timestamp()
            self.validate()

            # Publish domain event
            self._record_event(
                SectionDeactivated(
                    aggregate_id=self.id,
                    occurred_at=datetime.now(),
                )
            )

    def update_name(self, name: str) -> None:
        if self.name != name:
            old_name = self.name
            old_slug = self.slug

            self.name = name
            self.slug = SlugValueObject.from_name(name)
            self.update_timestamp()
            self.validate()

            # Publish domain event
            self._record_event(
                SectionNameUpdated(
                    aggregate_id=self.id,
                    occurred_at=datetime.now(),
                    old_name=old_name,
                    new_name=self.name,
                    old_slug=old_slug,
                    new_slug=self.slug,
                )
            )

    def update_description(self, description: str) -> None:
        if self.description != description:
            old_description = self.description

            self.description = description
            self.update_timestamp()
            self.validate()

            # Publish domain event
            self._record_event(
                SectionDescriptionUpdated(
                    aggregate_id=self.id,
                    occurred_at=datetime.now(),
                    old_description=old_description,
                    new_description=self.description,
                )
            )
