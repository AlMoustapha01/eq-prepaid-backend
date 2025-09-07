"""Section mapper for domain-persistence-response conversions."""

from core.db import BaseMapper
from modules.rules.domain.models.section import SectionEntity
from modules.rules.domain.value_objects.slug import SlugValueObject
from modules.rules.infrastructure.models.section_model import SectionModel


class SectionMapper(BaseMapper[SectionEntity, SectionModel, dict]):
    """Mapper for SectionEntity conversions."""

    def to_domain(self, persistence_model: SectionModel) -> SectionEntity:
        """Convert persistence model to domain entity."""
        return SectionEntity(
            id=persistence_model.id,
            created_at=persistence_model.created_at,
            updated_at=persistence_model.updated_at,
            name=persistence_model.name,
            slug=SlugValueObject(persistence_model.slug),
            description=persistence_model.description,
            status=persistence_model.status,
        )

    def to_persistence(self, domain_entity: SectionEntity) -> SectionModel:
        """Convert domain entity to persistence model."""
        model = SectionModel(
            name=domain_entity.name,
            slug=domain_entity.slug.value if domain_entity.slug else "",
            description=domain_entity.description,
            status=domain_entity.status.value if domain_entity.status else None,
        )

        # Set ID if exists (for updates)
        if domain_entity.id:
            model.id = domain_entity.id
        if domain_entity.created_at:
            model.created_at = domain_entity.created_at
        if domain_entity.updated_at:
            model.updated_at = domain_entity.updated_at

        return model

    def to_response(self, domain_entity: SectionEntity) -> dict:
        """Convert domain entity to response DTO."""
        return {
            "id": str(domain_entity.id),
            "name": domain_entity.name,
            "slug": domain_entity.slug.value if domain_entity.slug else None,
            "description": domain_entity.description,
            "status": domain_entity.status,
            "created_at": domain_entity.created_at.isoformat()
            if domain_entity.created_at
            else None,
            "updated_at": domain_entity.updated_at.isoformat()
            if domain_entity.updated_at
            else None,
        }
