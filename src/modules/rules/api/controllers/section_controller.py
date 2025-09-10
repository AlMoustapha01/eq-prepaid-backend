"""Section controller for handling section API operations."""

import logging
from uuid import UUID

from modules.rules.api.errors.exception_manager import exception_manager
from modules.rules.application.dtos.section_dtos import CreateSectionRequest, SectionResponse
from modules.rules.application.use_cases.section_use_cases import (
    CreateSectionUseCase,
    GetAllSectionsUseCase,
    GetSectionByIdUseCase,
)
from modules.rules.infrastructure.repositories.section_repository import SectionRepositoryPort

logger = logging.getLogger(__name__)


class SectionController:
    """Controller for section operations."""

    def __init__(self, section_repository: SectionRepositoryPort):
        self.section_repository = section_repository
        self.create_section_use_case = CreateSectionUseCase(section_repository)
        self.get_all_sections_use_case = GetAllSectionsUseCase(section_repository)
        self.get_section_by_id_use_case = GetSectionByIdUseCase(section_repository)

    async def create_section(self, request: CreateSectionRequest) -> SectionResponse:
        """
        Create a new section.

        Args:
            request: Section creation request

        Returns:
            Created section response

        Raises:
            HTTPException: If creation fails

        """
        try:
            logger.info("Creating section with name %s", request.name)
            return await self.create_section_use_case.execute(request)
        except Exception as e:
            logger.error("Section creation failed %s", e)
            raise exception_manager.handle_exception(e) from e

    async def get_all_sections(self) -> list[SectionResponse]:
        """
        Get all sections.

        Returns:
            List of section responses

        Raises:
            HTTPException: If retrieval fails

        """
        try:
            logger.info("Getting all sections")
            return await self.get_all_sections_use_case.execute()
        except Exception as e:
            logger.error("Error getting all sections %s", e)
            raise exception_manager.handle_exception(e) from e

    async def get_section_by_id(self, section_id: UUID) -> SectionResponse:
        """
        Get section by ID.

        Args:
            section_id: Section ID

        Returns:
            Section response

        Raises:
            HTTPException: If section not found or retrieval fails

        """
        try:
            logger.info("Getting section by ID %s", section_id)
            return await self.get_section_by_id_use_case.execute(section_id)
        except Exception as e:
            logger.error("Error getting section by ID %s", section_id)
            raise exception_manager.handle_exception(e) from e
