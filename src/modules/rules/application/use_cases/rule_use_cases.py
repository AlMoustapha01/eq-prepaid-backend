"""Rule use cases implementation."""

import logging
from typing import Any
from uuid import UUID

from core.db import PaginatedResult, PaginationParams
from modules.rules.domain.models.rule import CreateRuleDto, RuleEntity
from modules.rules.domain.value_objects.rule_config import RuleConfig
from modules.rules.infrastructure.mappers.rule_mapper import RuleMapper
from modules.rules.infrastructure.repositories.rule_repository import RuleRepositoryPort
from src.modules.rules.application.dtos.rule_dtos import (
    CreateRuleRequest,
    GetRulesSqlResponse,
    RuleResponse,
)

logger = logging.getLogger(__name__)


class CreateRuleUseCase:
    """Use case for creating a new rule."""

    def __init__(self, rule_repository: RuleRepositoryPort):
        self.rule_repository = rule_repository
        self.mapper = RuleMapper()

    async def execute(self, request: CreateRuleRequest) -> RuleResponse:
        """
        Create a new rule.

        Args:
            request: Rule creation request

        Returns:
            Created rule response

        Raises:
            ValueError: If rule name already exists or validation fails

        """
        logger.info(f"Creating rule with name: {request.name}")

        # Check if rule with same name already exists
        existing_rule = await self.rule_repository.find_by_name(request.name)
        if existing_rule:
            from modules.rules.domain.exceptions import RuleAlreadyExistsError

            raise RuleAlreadyExistsError(rule_name=request.name)

        # Convert config dict to RuleConfig
        try:
            rule_config = RuleConfig.from_dict(request.config)
        except Exception as e:
            from modules.rules.domain.exceptions import RuleConfigurationError

            msg = f"Invalid rule configuration: {e!s}"
            raise RuleConfigurationError(msg)

        # Create domain DTO
        create_dto = CreateRuleDto(
            name=request.name,
            profile_type=request.profile_type,
            balance_type=request.balance_type,
            database_table_name=request.database_table_name,
            section_id=request.section_id,
            config=rule_config,
        )

        # Create domain entity
        rule_entity = RuleEntity.create(create_dto)

        # Save to repository
        created_rule = await self.rule_repository.insert_one(rule_entity)

        # Convert to response
        response_dict = self.mapper.to_response(created_rule)
        return RuleResponse(**response_dict)


class GetAllRulesPaginatedUseCase:
    """Use case for getting all rules with pagination."""

    def __init__(self, rule_repository: RuleRepositoryPort):
        self.rule_repository = rule_repository
        self.mapper = RuleMapper()

    async def execute(
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

        """
        logger.info(f"Getting rules - page: {page}, size: {size}")

        # Create pagination params
        pagination = PaginationParams(page=page, size=size)

        # Get paginated rules from repository
        paginated_rules = await self.rule_repository.find_all_paginated(
            pagination=pagination, filters=filters
        )

        # Convert to responses
        responses = []
        for rule in paginated_rules.items:
            response_dict = self.mapper.to_response(rule)
            responses.append(RuleResponse(**response_dict))

        # Return paginated result with responses
        return PaginatedResult(
            items=responses,
            total=paginated_rules.total,
            page=paginated_rules.page,
            size=paginated_rules.size,
        )


class GetRuleSqlByIdUseCase:
    """Use case for getting rule SQL by rule ID."""

    def __init__(self, rule_repository: RuleRepositoryPort):
        self.rule_repository = rule_repository

    async def execute(
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
            ValueError: If rule not found

        """
        logger.info(f"Getting SQL for rule ID: {rule_id}")

        # Find rule by ID
        rule = await self.rule_repository.find_by_id(rule_id)
        if not rule:
            from modules.rules.domain.exceptions import RuleNotFoundError

            raise RuleNotFoundError(rule_id=rule_id)

        # Generate SQL
        try:
            sql = rule.generate_sql(parameters or {})
        except Exception as e:
            from modules.rules.domain.exceptions import RuleSqlGenerationError

            msg = f"Failed to generate SQL: {e!s}"
            raise RuleSqlGenerationError(msg, rule_id=rule_id)

        # Create response
        return GetRulesSqlResponse(
            rule_id=str(rule.id), rule_name=rule.name, sql=sql, parameters_used=parameters
        )


class GetRuleByIdUseCase:
    """Use case for getting a rule by ID."""

    def __init__(self, rule_repository: RuleRepositoryPort):
        self.rule_repository = rule_repository
        self.mapper = RuleMapper()

    async def execute(self, rule_id: UUID) -> RuleResponse:
        """
        Get rule by ID.

        Args:
            rule_id: Rule ID

        Returns:
            Rule response

        Raises:
            ValueError: If rule not found

        """
        logger.info(f"Getting rule by ID: {rule_id}")

        # Find rule by ID
        rule = await self.rule_repository.find_by_id(rule_id)
        if not rule:
            from modules.rules.domain.exceptions import RuleNotFoundError

            raise RuleNotFoundError(rule_id=rule_id)

        # Convert to response
        response_dict = self.mapper.to_response(rule)
        return RuleResponse(**response_dict)
