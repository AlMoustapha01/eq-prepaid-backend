"""Rule DTOs for application layer."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel

from modules.rules.domain.value_objects.enums import BalanceType, ProfileType


class CreateRuleRequest(BaseModel):
    """Request DTO for creating a rule."""

    name: str
    profile_type: ProfileType
    balance_type: BalanceType
    database_table_name: list[str]
    section_id: UUID
    config: dict[str, Any]  # Will be converted to RuleConfig


class RuleResponse(BaseModel):
    """Response DTO for rule data."""

    id: str
    name: str
    profile_type: str
    balance_type: str
    database_table_name: list[str]
    section_id: str
    config: dict[str, Any] | None
    status: str
    created_at: str
    updated_at: str | None


class GetRulesSqlResponse(BaseModel):
    """Response DTO for rule SQL generation."""

    rule_id: str
    rule_name: str
    sql: str
    parameters_used: dict[str, Any] | None
