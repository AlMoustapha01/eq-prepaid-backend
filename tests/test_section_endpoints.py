"""End-to-end tests for section endpoints."""

import pytest
from fastapi import status
from httpx import AsyncClient

from modules.rules.application.dtos.section_dtos import SectionResponse


class TestSectionEndpoints:
    """Test class for section API endpoints."""

    @pytest.mark.asyncio
    async def test_create_section_success(self, async_client: AsyncClient, sample_section_data):
        """Test successful section creation."""
        response = await async_client.post("/api/v1/sections/", json=sample_section_data)

        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert data["name"] == sample_section_data["name"]
        assert data["description"] == sample_section_data["description"]
        assert "id" in data
        assert "slug" in data
        assert data["status"] == "ACTIVE"
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_section_invalid_data(self, async_client: AsyncClient):
        """Test section creation with invalid data."""
        invalid_data = {"name": ""}  # Missing description and empty name

        response = await async_client.post("/api/v1/sections/", json=invalid_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_get_all_sections_empty(self, async_client: AsyncClient):
        """Test getting all sections when none exist."""
        response = await async_client.get("/api/v1/sections/")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_all_sections_with_data(self, async_client: AsyncClient, sample_section_data):
        """Test getting all sections when sections exist."""
        # Create a section first
        create_response = await async_client.post("/api/v1/sections/", json=sample_section_data)
        assert create_response.status_code == status.HTTP_201_CREATED

        # Get all sections
        response = await async_client.get("/api/v1/sections/")

        assert response.status_code == status.HTTP_200_OK
        sections = response.json()
        assert len(sections) == 1
        assert sections[0]["name"] == sample_section_data["name"]

    @pytest.mark.asyncio
    async def test_get_section_by_id_success(self, async_client: AsyncClient, sample_section_data):
        """Test getting a section by ID successfully."""
        # Create a section first
        create_response = await async_client.post("/api/v1/sections/", json=sample_section_data)
        assert create_response.status_code == status.HTTP_201_CREATED
        section_id = create_response.json()["id"]

        # Get section by ID
        response = await async_client.get(f"/api/v1/sections/{section_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == section_id
        assert data["name"] == sample_section_data["name"]

    @pytest.mark.asyncio
    async def test_get_section_by_id_not_found(self, async_client: AsyncClient):
        """Test getting a section by ID that doesn't exist."""
        non_existent_id = "550e8400-e29b-41d4-a716-446655440000"

        response = await async_client.get(f"/api/v1/sections/{non_existent_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_section_by_invalid_id(self, async_client: AsyncClient):
        """Test getting a section with invalid UUID format."""
        invalid_id = "invalid-uuid"

        response = await async_client.get(f"/api/v1/sections/{invalid_id}")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_create_multiple_sections(self, async_client: AsyncClient):
        """Test creating multiple sections and retrieving them."""
        sections_data = [
            {"name": "Section 1", "description": "First section"},
            {"name": "Section 2", "description": "Second section"},
            {"name": "Section 3", "description": "Third section"},
        ]

        created_sections = []
        for section_data in sections_data:
            response = await async_client.post("/api/v1/sections/", json=section_data)
            assert response.status_code == status.HTTP_201_CREATED
            created_sections.append(response.json())

        # Get all sections
        response = await async_client.get("/api/v1/sections/")
        assert response.status_code == status.HTTP_200_OK

        all_sections = response.json()
        assert len(all_sections) == 3

        # Verify all sections are present
        section_names = {section["name"] for section in all_sections}
        expected_names = {section["name"] for section in sections_data}
        assert section_names == expected_names

    @pytest.mark.asyncio
    async def test_section_response_schema(self, async_client: AsyncClient, sample_section_data):
        """Test that section response matches expected schema."""
        response = await async_client.post("/api/v1/sections/", json=sample_section_data)
        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()

        # Validate response can be parsed as SectionResponse
        section_response = SectionResponse(**data)
        assert section_response.name == sample_section_data["name"]
        assert section_response.description == sample_section_data["description"]
        assert section_response.status == "ACTIVE"
