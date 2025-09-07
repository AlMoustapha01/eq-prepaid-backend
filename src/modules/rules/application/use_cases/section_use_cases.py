"""Section use cases implementation."""

import logging
from uuid import UUID

from core.db import PaginationParams
from modules.rules.application.dtos.section_dtos import (
    CreateSectionRequest,
    SectionResponse,
)
from modules.rules.domain.models.section import CreateSectionDto, SectionEntity
from modules.rules.infrastructure.mappers.section_mapper import SectionMapper
from modules.rules.infrastructure.repositories.section_repository import (
    SectionRepositoryPort,
)

logger = logging.getLogger(__name__)


class CreateSectionUseCase:
    """Use case for creating a new section."""

    def __init__(self, section_repository: SectionRepositoryPort):
        self.section_repository = section_repository
        self.mapper = SectionMapper()

    async def execute(self, request: CreateSectionRequest) -> SectionResponse:
        """
        Create a new section.

        Args:
            request: Section creation request

        Returns:
            Created section response

        Raises:
            ValueError: If section name already exists

        """
        logger.info("Creating section with name %s", request.name)

        # Check if section with same name already exists
        existing_section = await self.section_repository.find_by_name(request.name)
        if existing_section:
            from modules.rules.domain.exceptions import SectionAlreadyExistsError

            raise SectionAlreadyExistsError(section_name=request.name)

        # Create domain DTO
        create_dto = CreateSectionDto(name=request.name, description=request.description)

        # Create domain entity
        section_entity = SectionEntity.create(create_dto)

        # Save to repository
        created_section = await self.section_repository.insert_one(section_entity)

        # Convert to response
        response_dict = self.mapper.to_response(created_section)
        return SectionResponse(**response_dict)


class GetAllSectionsUseCase:
    """Use case for getting all sections."""

    def __init__(self, section_repository: SectionRepositoryPort):
        self.section_repository = section_repository
        self.mapper = SectionMapper()

    async def execute(self) -> list[SectionResponse]:
        """
        Get all sections.

        Returns:
            List of section responses

        """
        logger.info("Getting all sections")

        # Get all sections from repository
        pagination = PaginationParams(page=1, size=100)  # Max allowed size
        sections = await self.section_repository.find_all_paginated(pagination=pagination)

        # Convert to responses
        responses = []
        for section in sections.items:
            response_dict = self.mapper.to_response(section)
            responses.append(SectionResponse(**response_dict))

        logger.info("Found %s sections", len(responses))
        return responses


class GetSectionByIdUseCase:
    """Use case for getting a section by ID."""

    def __init__(self, section_repository: SectionRepositoryPort):
        self.section_repository = section_repository
        self.mapper = SectionMapper()

    async def execute(self, section_id: UUID) -> SectionResponse:
        """
        Get section by ID.

        Args:
            section_id: Section ID

        Returns:
            Section response

        Raises:
            ValueError: If section not found

        """
        logger.info("Getting section by ID %s", section_id)

        # Find section by ID
        section = await self.section_repository.find_by_id(section_id)
        if not section:
            from modules.rules.domain.exceptions import SectionNotFoundError

            raise SectionNotFoundError(section_id=section_id)

        # Convert to response
        response_dict = self.mapper.to_response(section)
        return SectionResponse(**response_dict)
