from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, field_validator

from core.domain.base_entity import BaseEntity

# SqlGenerator imported lazily to avoid circular imports
from modules.rules.domain.events.rule_events import (
    RuleArchived,
    RuleBalanceTypeUpdated,
    RuleConfigurationUpdated,
    RuleCreated,
    RuleDraftStarted,
    RuleNameUpdated,
    RuleProductionStarted,
    RuleProfileTypeUpdated,
    RuleToValidateStarted,
)
from modules.rules.domain.value_objects.enums import BalanceType, ProfileType, RuleStatus
from modules.rules.domain.value_objects.rule_config.root import RuleConfig


# ----------------------------------------------------
# DTO avec validations Pydantic
# ----------------------------------------------------
class CreateRuleDto(BaseModel):
    name: str
    profile_type: ProfileType
    balance_type: BalanceType
    database_table_name: list[str]
    section_id: UUID
    config: RuleConfig

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Rule name cannot be empty")
        if len(v) > 255:
            raise ValueError("Rule name too long (max 255 chars)")
        return v

    @field_validator("database_table_name")
    @classmethod
    def validate_tables(cls, v: list[str]) -> list[str]:
        if not v or len(v) == 0:
            raise ValueError("At least one database table is required")
        return v


# ----------------------------------------------------
# State Machine : valid transitions between statuses
# ----------------------------------------------------
ALLOWED_TRANSITIONS: dict[RuleStatus, list[RuleStatus]] = {
    RuleStatus.DRAFT: [RuleStatus.TO_VALIDATE],
    RuleStatus.TO_VALIDATE: [RuleStatus.IN_PRODUCTION, RuleStatus.DRAFT],
    RuleStatus.IN_PRODUCTION: [RuleStatus.ARCHIVED],
    RuleStatus.ARCHIVED: [],
}


@dataclass
class RuleEntity(BaseEntity):
    name: str = ""
    profile_type: ProfileType = None
    balance_type: BalanceType = None
    database_table_name: list[str] = field(default_factory=list)
    section_id: UUID = None
    config: RuleConfig = None
    status: RuleStatus = None

    def validate(self) -> None:
        """Validates that all business invariants of the entity are respected"""
        super().validate()
        self._ensure_rule_has_valid_configuration()
        self._ensure_rule_has_valid_business_context()
        self._ensure_prepaid_profile_has_only_main_balance()
        self._ensure_database_tables_are_valid()
        self._ensure_config_tables_match_database_tables()

    def _ensure_rule_has_valid_configuration(self) -> None:
        """A rule must have a valid SQL configuration"""
        if not self.name or not self.name.strip():
            raise ValueError("A rule must have a name")

        if not self.config:
            raise ValueError("A rule must have a configuration")

        # Validate the RuleConfig itself
        self.config.validate()

    def _ensure_rule_has_valid_business_context(self) -> None:
        """A rule must have valid business context"""
        if not self.section_id:
            raise ValueError("A rule must be associated with a section")

        if not isinstance(self.profile_type, ProfileType):
            raise ValueError("A rule must have a valid profile type")

        if not isinstance(self.balance_type, BalanceType):
            raise ValueError("A rule must have a valid balance type")

    def _ensure_prepaid_profile_has_only_main_balance(self) -> None:
        """Prepaid profile can only have main balance"""
        if (
            self.profile_type == ProfileType.PREPAID
            and self.balance_type != BalanceType.MAIN_BALANCE
        ):
            raise ValueError("Prepaid profile can only have main balance")

    def _ensure_database_tables_are_valid(self) -> None:
        """A rule must specify at least one database table"""
        if not self.database_table_name or len(self.database_table_name) == 0:
            raise ValueError("A rule must specify at least one database table")

    def _ensure_config_tables_match_database_tables(self) -> None:
        """All tables used in configuration must be listed in database_table_name"""
        if not self.config:
            return
        missing = set(self.config.get_table_names()) - set(self.database_table_name)
        if missing:
            raise ValueError(
                f"Tables {missing} used in configuration but not listed in database_table_name"
            )

    def _change_status(self, new_status: RuleStatus, event_cls) -> None:
        """State machine : applique une transition de statut si valide."""
        if new_status == self.status:
            return  # pas de changement inutile
        if new_status not in ALLOWED_TRANSITIONS.get(self.status, []):
            raise ValueError(f"Invalid transition: {self.status} → {new_status}")

        old_status = self.status
        self.status = new_status

        self.update_timestamp()
        self.validate()

        # Publish domain event
        event = event_cls(
            aggregate_id=self.id,
            occurred_at=datetime.now(),
            rule_name=self.name,
            old_status=old_status,
            new_status=new_status,
        )
        self._record_event(event)

    def get_required_parameters(self) -> list[str]:
        """Returns list of required parameter names for this rule"""
        return self.config.get_required_parameters()

    def get_parameter_info(self) -> dict[str, dict[str, Any]]:
        """Returns detailed information about all parameters"""
        return {
            name: {
                "type": param.type.value,
                "required": param.required,
                "default": param.default,
                "description": param.description,
                "values": param.values,
            }
            for name, param in self.config.parameters.items()
        }

    def update_name(self, new_name: str) -> None:
        """Updates the rule name"""
        if self.name != new_name:
            old_name = self.name
            self.name = new_name
            self.update_timestamp()
            self.validate()

            # Publish domain event
            event = RuleNameUpdated(
                aggregate_id=self.id,
                occurred_at=datetime.now(),
                old_name=old_name,
                new_name=self.name,
            )
            self._record_event(event)

    def update_profile_type(self, new_profile_type: ProfileType) -> None:
        """Updates the rule profile type"""
        if self.profile_type != new_profile_type:
            old_profile_type = self.profile_type
            self.profile_type = new_profile_type
            self.update_timestamp()
            self.validate()

            # Publish domain event
            event = RuleProfileTypeUpdated(
                aggregate_id=self.id,
                occurred_at=datetime.now(),
                old_profile_type=old_profile_type.value,
                new_profile_type=self.profile_type.value,
            )
            self._record_event(event)

    def update_balance_type(self, new_balance_type: BalanceType) -> None:
        """Updates the rule balance type"""
        if self.balance_type != new_balance_type:
            old_balance_type = self.balance_type
            self.balance_type = new_balance_type
            self.update_timestamp()
            self.validate()

            # Publish domain event
            event = RuleBalanceTypeUpdated(
                aggregate_id=self.id,
                occurred_at=datetime.now(),
                old_balance_type=old_balance_type.value,
                new_balance_type=self.balance_type.value,
            )
            self._record_event(event)

    def update_configuration(self, new_config: RuleConfig) -> None:
        """Updates the rule configuration"""
        self.config = new_config
        self.update_timestamp()
        self.validate()

        # Publish domain event
        event = RuleConfigurationUpdated(
            aggregate_id=self.id,
            occurred_at=datetime.now(),
            rule_name=self.name,
        )
        self._record_event(event)

    def move_to_production(self) -> None:
        self._change_status(RuleStatus.IN_PRODUCTION, RuleProductionStarted)

    def move_to_validation(self) -> None:
        self._change_status(RuleStatus.TO_VALIDATE, RuleToValidateStarted)

    def move_to_draft(self) -> None:
        self._change_status(RuleStatus.DRAFT, RuleDraftStarted)

    def move_to_archived(self) -> None:
        self._change_status(RuleStatus.ARCHIVED, RuleArchived)

    @classmethod
    def create(cls, dto: CreateRuleDto) -> "RuleEntity":
        """Creates a new RuleEntity from a DTO"""
        entity = cls(
            id=uuid4(),
            name=dto.name,
            profile_type=dto.profile_type,
            balance_type=dto.balance_type,
            database_table_name=dto.database_table_name,
            section_id=dto.section_id,
            config=dto.config,
            status=RuleStatus.DRAFT,
        )

        # Ensure validation is performed
        entity.validate()

        # Publish domain event
        event = RuleCreated(
            aggregate_id=entity.id,
            occurred_at=datetime.now(),
            name=entity.name,
            profile_type=entity.profile_type,
            balance_type=entity.balance_type,
            section_id=entity.section_id,
            status=entity.status,
        )
        entity._record_event(event)

        return entity
