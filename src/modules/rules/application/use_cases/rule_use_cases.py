"""Rule use cases implementation."""

import logging
from typing import Any, NoReturn
from uuid import UUID

from core.db import PaginatedResult, PaginationParams
from modules.rules.domain.models.rule import CreateRuleDto, RuleEntity
from modules.rules.domain.value_objects.rule_config.root import RuleConfig
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
        logger.info("Creating rule with name: %s", request.name)

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
            raise RuleConfigurationError(msg) from e

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
        logger.info("Getting rules - page: %s, size: %s", page, size)

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

    def _raise_config_error(self, msg: str) -> NoReturn:
        from modules.rules.domain.exceptions import RuleSqlGenerationError

        raise RuleSqlGenerationError(msg, rule_id=self.rule_id)

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
        logger.info("Getting SQL for rule ID: %s", rule_id)

        rule = await self.rule_repository.find_by_id(rule_id)
        if not rule:
            from modules.rules.domain.exceptions import RuleNotFoundError

            raise RuleNotFoundError(rule_id=rule_id)

        self.rule_id = rule_id

        try:
            if not rule.config:
                self._raise_config_error("Rule configuration is missing")

            if isinstance(rule.config, dict):
                rule_config = RuleConfig.from_dict(rule.config)
            elif isinstance(rule.config, RuleConfig):
                rule_config = rule.config
            else:
                self._raise_config_error("Invalid rule configuration format")

            sql = rule_config.to_sql()

        except Exception as e:
            self._raise_config_error("Failed to generate SQL: " + str(e))

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
        logger.info("Getting rule by ID: %s", rule_id)

        # Find rule by ID
        rule = await self.rule_repository.find_by_id(rule_id)
        if not rule:
            from modules.rules.domain.exceptions import RuleNotFoundError

            raise RuleNotFoundError(rule_id=rule_id)

        # Convert to response
        response_dict = self.mapper.to_response(rule)
        return RuleResponse(**response_dict)
