"""Section DTOs for application layer."""

from pydantic import BaseModel


class CreateSectionRequest(BaseModel):
    """Request DTO for creating a section."""

    name: str
    description: str


class SectionResponse(BaseModel):
    """Response DTO for section data."""

    id: str
    name: str
    slug: str
    description: str | None
    status: str
    created_at: str
    updated_at: str | None
