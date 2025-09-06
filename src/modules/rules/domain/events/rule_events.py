from dataclasses import dataclass
from typing import Any
from uuid import UUID

from core.domain.domain_event import DomainEvent
from modules.rules.domain.value_objects.enums import BalanceType, ProfileType, Status


@dataclass
class RuleCreated(DomainEvent):
    """Event raised when a rule is created"""

    aggregate_id: UUID = None
    name: str = ""
    profile_type: ProfileType = None
    balance_type: BalanceType = None
    section_id: UUID = None
    status: Status = None

    def get_event_type(self) -> str:
        return "rule.created"

    def _get_event_data(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "profile_type": self.profile_type.value,
            "balance_type": self.balance_type.value,
            "section_id": str(self.section_id),
            "status": self.status.value,
        }


@dataclass
class RuleConfigurationUpdated(DomainEvent):
    """Event raised when a rule's configuration is updated"""

    aggregate_id: UUID = None
    rule_name: str = ""

    def get_event_type(self) -> str:
        return "rule.configuration_updated"

    def _get_event_data(self) -> dict[str, Any]:
        return {"rule_name": self.rule_name}


@dataclass
class RuleNameUpdated(DomainEvent):
    """Event raised when a rule's name is updated"""

    aggregate_id: UUID = None
    old_name: str = ""
    new_name: str = ""

    def get_event_type(self) -> str:
        return "rule.name_updated"

    def _get_event_data(self) -> dict[str, Any]:
        return {"old_name": self.old_name, "new_name": self.new_name}


@dataclass
class RuleProfileTypeUpdated(DomainEvent):
    """Event raised when a rule's profile type is updated"""

    aggregate_id: UUID = None
    old_profile_type: ProfileType = None
    new_profile_type: ProfileType = None

    def get_event_type(self) -> str:
        return "rule.profile_type_updated"

    def _get_event_data(self) -> dict[str, Any]:
        return {
            "old_profile_type": self.old_profile_type.value,
            "new_profile_type": self.new_profile_type.value,
        }


@dataclass
class RuleBalanceTypeUpdated(DomainEvent):
    """Event raised when a rule's balance type is updated"""

    aggregate_id: UUID = None
    old_balance_type: BalanceType = None
    new_balance_type: BalanceType = None

    def get_event_type(self) -> str:
        return "rule.balance_type_updated"

    def _get_event_data(self) -> dict[str, Any]:
        return {
            "old_balance_type": self.old_balance_type.value,
            "new_balance_type": self.new_balance_type.value,
        }


@dataclass
class RuleSqlGenerated(DomainEvent):
    """Event raised when SQL is generated from a rule"""

    aggregate_id: UUID = None
    rule_name: str = ""
    parameters_count: int = 0

    def get_event_type(self) -> str:
        return "rule.sql_generated"

    def _get_event_data(self) -> dict[str, Any]:
        return {"rule_name": self.rule_name, "parameters_count": self.parameters_count}


@dataclass
class RuleProductionStarted(DomainEvent):
    """Event raised when a rule is moved to production status"""

    aggregate_id: UUID = None
    rule_name: str = ""

    def get_event_type(self) -> str:
        return "rule.production_started"

    def _get_event_data(self) -> dict[str, Any]:
        return {"rule_name": self.rule_name}


@dataclass
class RuleToValidateStarted(DomainEvent):
    """Event raised when a rule is moved to validation status"""

    aggregate_id: UUID = None
    rule_name: str = ""

    def get_event_type(self) -> str:
        return "rule.to_validate_started"

    def _get_event_data(self) -> dict[str, Any]:
        return {"rule_name": self.rule_name}


@dataclass
class RuleDraftStarted(DomainEvent):
    """Event raised when a rule is moved to draft status"""

    aggregate_id: UUID = None
    rule_name: str = ""

    def get_event_type(self) -> str:
        return "rule.draft_started"

    def _get_event_data(self) -> dict[str, Any]:
        return {"rule_name": self.rule_name}
