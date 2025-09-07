"""Rule API routes."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from core.db import PaginatedResult
from modules.rules.api.controllers.rule_controller import RuleController
from modules.rules.api.dependencies import get_rule_repository
from modules.rules.application.dtos.rule_dtos import (
    CreateRuleRequest,
    GetRulesSqlResponse,
    RuleResponse,
)
from modules.rules.infrastructure.repositories.rule_repository import RuleRepository

rule_router = APIRouter(prefix="/rules", tags=["rules"])


@rule_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new rule",
    description="Create a new rule with configuration",
)
async def create_rule(
    request: CreateRuleRequest,
    rule_repository: Annotated[RuleRepository, Depends(get_rule_repository)],
) -> RuleResponse:
    """Create a new rule."""
    controller = RuleController(rule_repository)
    return await controller.create_rule(request)


@rule_router.get(
    "/",
    summary="Get all rules with pagination",
    description="Retrieve all rules with pagination support",
)
async def get_all_rules_paginated(
    rule_repository: Annotated[RuleRepository, Depends(get_rule_repository)],
    page: Annotated[int, Query(ge=1, description="Page number (1-based)")] = 1,
    size: Annotated[int, Query(ge=1, le=100, description="Page size")] = 10,
    status_filter: Annotated[str | None, Query(description="Filter by status")] = None,
    profile_type_filter: Annotated[str | None, Query(description="Filter by profile type")] = None,
    balance_type_filter: Annotated[str | None, Query(description="Filter by balance type")] = None,
) -> PaginatedResult[RuleResponse]:
    """Get all rules with pagination."""
    # Build filters
    filters = {}
    if status_filter:
        filters["status"] = {"eq": status_filter}
    if profile_type_filter:
        filters["profile_type"] = {"eq": profile_type_filter}
    if balance_type_filter:
        filters["balance_type"] = {"eq": balance_type_filter}

    controller = RuleController(rule_repository)
    return await controller.get_all_rules_paginated(page, size, filters if filters else None)


@rule_router.get(
    "/{rule_id}",
    summary="Get rule by ID",
    description="Retrieve a specific rule by its ID",
)
async def get_rule_by_id(
    rule_id: UUID, rule_repository: Annotated[RuleRepository, Depends(get_rule_repository)]
) -> RuleResponse:
    """Get rule by ID."""
    controller = RuleController(rule_repository)
    return await controller.get_rule_by_id(rule_id)


@rule_router.post(
    "/{rule_id}/sql",
    summary="Get rule SQL by ID",
    description="Generate SQL query from rule configuration with optional parameters",
)
async def get_rule_sql_by_id(
    rule_id: UUID,
    parameters: dict[str, Any] | None = None,
    rule_repository: Annotated[RuleRepository, Depends(get_rule_repository)] = None,
) -> GetRulesSqlResponse:
    """Get rule SQL by ID with optional parameters."""
    if rule_repository is None:
        rule_repository = get_rule_repository()

    controller = RuleController(rule_repository)
    return await controller.get_rule_sql_by_id(rule_id, parameters)
