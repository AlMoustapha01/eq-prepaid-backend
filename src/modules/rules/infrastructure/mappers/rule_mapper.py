"""Rule mapper for domain-persistence-response conversions."""

from core.db import BaseMapper
from modules.rules.domain.models.rule import RuleEntity
from modules.rules.domain.value_objects.rule_config import RuleConfig
from src.modules.rules.infrastructure.models.rule_model import RuleModel


class RuleMapper(BaseMapper[RuleEntity, RuleModel, dict]):
    """Mapper for RuleEntity conversions."""

    def to_domain(self, persistence_model: RuleModel) -> RuleEntity:
        """Convert persistence model to domain entity."""
        # Deserialize config from JSON to RuleConfig
        config = None
        if persistence_model.config:
            config = RuleConfig.from_dict(persistence_model.config)

        return RuleEntity(
            id=persistence_model.id,
            created_at=persistence_model.created_at,
            updated_at=persistence_model.updated_at,
            name=persistence_model.name,
            profile_type=persistence_model.profile_type,
            balance_type=persistence_model.balance_type,
            database_table_name=persistence_model.database_table_name,
            section_id=persistence_model.section_id,
            config=config,
            status=persistence_model.status,
        )

    def to_persistence(self, domain_entity: RuleEntity) -> RuleModel:
        """Convert domain entity to persistence model."""
        # Serialize config to JSON
        config_dict = None
        if domain_entity.config:
            config_dict = domain_entity.config.to_dict()

        model = RuleModel(
            name=domain_entity.name,
            profile_type=domain_entity.profile_type,
            balance_type=domain_entity.balance_type,
            database_table_name=domain_entity.database_table_name,
            section_id=domain_entity.section_id,
            config=config_dict,
            status=domain_entity.status,
        )

        # Set ID if exists (for updates)
        if domain_entity.id:
            model.id = domain_entity.id
        if domain_entity.created_at:
            model.created_at = domain_entity.created_at
        if domain_entity.updated_at:
            model.updated_at = domain_entity.updated_at

        return model

    def to_response(self, domain_entity: RuleEntity) -> dict:
        """Convert domain entity to response DTO."""
        return {
            "id": str(domain_entity.id),
            "name": domain_entity.name,
            "profile_type": domain_entity.profile_type.value
            if domain_entity.profile_type
            else None,
            "balance_type": domain_entity.balance_type.value
            if domain_entity.balance_type
            else None,
            "database_table_name": domain_entity.database_table_name,
            "section_id": str(domain_entity.section_id) if domain_entity.section_id else None,
            "config": domain_entity.config.to_dict() if domain_entity.config else None,
            "status": domain_entity.status.value if domain_entity.status else None,
            "created_at": domain_entity.created_at.isoformat()
            if domain_entity.created_at
            else None,
            "updated_at": domain_entity.updated_at.isoformat()
            if domain_entity.updated_at
            else None,
        }
