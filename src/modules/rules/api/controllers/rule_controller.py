"""Rule controller for handling rule API operations."""

import logging
from typing import Any
from uuid import UUID

from core.db import PaginatedResult
from modules.rules.api.errors.exception_manager import exception_manager
from modules.rules.application.dtos.rule_dtos import (
    CreateRuleRequest,
    GetRulesSqlResponse,
    RuleResponse,
)
from modules.rules.application.use_cases.rule_use_cases import (
    CreateRuleUseCase,
    GetAllRulesPaginatedUseCase,
    GetRuleByIdUseCase,
    GetRuleSqlByIdUseCase,
)
from modules.rules.infrastructure.repositories.rule_repository import RuleRepositoryPort

logger = logging.getLogger(__name__)


class RuleController:
    """Controller for rule operations."""

    def __init__(self, rule_repository: RuleRepositoryPort):
        self.rule_repository = rule_repository
        self.create_rule_use_case = CreateRuleUseCase(rule_repository)
        self.get_all_rules_paginated_use_case = GetAllRulesPaginatedUseCase(rule_repository)
        self.get_rule_sql_by_id_use_case = GetRuleSqlByIdUseCase(rule_repository)
        self.get_rule_by_id_use_case = GetRuleByIdUseCase(rule_repository)

    async def create_rule(self, request: CreateRuleRequest) -> RuleResponse:
        """
        Create a new rule.

        Args:
            request: Rule creation request

        Returns:
            Created rule response

        Raises:
            HTTPException: If creation fails

        """
        try:
            logger.info("Creating rule %s", request.name)
            return await self.create_rule_use_case.execute(request)
        except Exception as e:
            logger.error("Rule creation failed")
            raise exception_manager.handle_exception(e) from e

    async def get_all_rules_paginated(
        self, page: int = 1, size: int = 10, filters: dict[str, Any] | None = None
    ) -> PaginatedResult[RuleResponse]:
        """
        Get all rules with pagination.

        Args:
            page: Page number (1-based)
            size: Page size
            filters: Optional filters to apply

        Returns:
            Paginated result of rule responses

        Raises:
            HTTPException: If retrieval fails

        """
        try:
            logger.info("Getting paginated rules - page: %s, size: %s", page, size)
            return await self.get_all_rules_paginated_use_case.execute(page, size, filters)
        except Exception as e:
            logger.exception("Error getting paginated rules")
            raise exception_manager.handle_exception(e) from e

    async def get_rule_sql_by_id(
        self, rule_id: UUID, parameters: dict[str, Any] | None = None
    ) -> GetRulesSqlResponse:
        """
        Get rule SQL by ID.

        Args:
            rule_id: Rule ID
            parameters: Optional parameters for SQL generation

        Returns:
            Rule SQL response

        Raises:
            HTTPException: If rule not found or SQL generation fails

        """
        try:
            logger.info("Getting SQL for rule ID %s", rule_id)
            return await self.get_rule_sql_by_id_use_case.execute(rule_id, parameters)
        except Exception as e:
            logger.exception("Error getting rule SQL")
            raise exception_manager.handle_exception(e) from e

    async def get_rule_by_id(self, rule_id: UUID) -> RuleResponse:
        """
        Get rule by ID.

        Args:
            rule_id: Rule ID

        Returns:
            Rule response

        Raises:
            HTTPException: If rule not found or retrieval fails

        """
        try:
            logger.info("Getting rule by ID %s", rule_id)
            return await self.get_rule_by_id_use_case.execute(rule_id)
        except Exception as e:
            logger.exception("Error getting rule by ID")
            raise exception_manager.handle_exception(e) from e
