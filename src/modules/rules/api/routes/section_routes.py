"""Section API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from modules.rules.api.controllers.section_controller import SectionController
from modules.rules.api.dependencies import get_section_repository
from modules.rules.application.dtos.section_dtos import CreateSectionRequest, SectionResponse
from modules.rules.infrastructure.repositories.section_repository import SectionRepository

section_router = APIRouter(prefix="/sections", tags=["sections"])


@section_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new section",
    description="Create a new section with name and description",
)
async def create_section(
    request: CreateSectionRequest,
    section_repository: Annotated[SectionRepository, Depends(get_section_repository)],
) -> SectionResponse:
    """Create a new section."""
    controller = SectionController(section_repository)
    return await controller.create_section(request)


@section_router.get(
    "/",
    summary="Get all sections",
    description="Retrieve all sections",
)
async def get_all_sections(
    section_repository: Annotated[SectionRepository, Depends(get_section_repository)],
) -> list[SectionResponse]:
    """Get all sections."""
    controller = SectionController(section_repository)
    return await controller.get_all_sections()


@section_router.get(
    "/{section_id}",
    summary="Get section by ID",
    description="Retrieve a specific section by its ID",
)
async def get_section_by_id(
    section_id: UUID,
    section_repository: Annotated[SectionRepository, Depends(get_section_repository)],
) -> SectionResponse:
    """Get section by ID."""
    controller = SectionController(section_repository)
    return await controller.get_section_by_id(section_id)
