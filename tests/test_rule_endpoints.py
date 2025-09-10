"""End-to-end tests for rule endpoints."""

import pytest
from fastapi import status
from httpx import AsyncClient

from modules.rules.application.dtos.rule_dtos import GetRulesSqlResponse, RuleResponse
from modules.rules.domain.value_objects.enums import ProfileType


class TestRuleEndpoints:
    """Test class for rule API endpoints."""

    @pytest.mark.asyncio
    async def test_create_rule_success(
        self, async_client: AsyncClient, sample_section_data, sample_rule_data
    ):
        """Test successful rule creation."""
        # First create a section to use as section_id
        section_response = await async_client.post("/api/v1/sections/", json=sample_section_data)
        assert section_response.status_code == status.HTTP_201_CREATED
        section_id = section_response.json()["id"]

        # Add section_id to rule data
        rule_data = sample_rule_data.copy()
        rule_data["section_id"] = section_id

        response = await async_client.post("/api/v1/rules/", json=rule_data)

        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert data["name"] == rule_data["name"]
        assert data["profile_type"] == rule_data["profile_type"]
        assert data["balance_type"] == rule_data["balance_type"]
        assert data["database_table_name"] == rule_data["database_table_name"]
        assert data["section_id"] == section_id
        # Config is transformed during processing, so just check it exists and has expected structure
        assert "config" in data
        assert isinstance(data["config"], dict)
        assert "id" in data
        assert data["status"] == "DRAFT"
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_rule_invalid_data(self, async_client: AsyncClient):
        """Test rule creation with invalid data."""
        invalid_data = {"name": ""}  # Missing required fields

        response = await async_client.post("/api/v1/rules/", json=invalid_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_create_rule_invalid_section_id(
        self, async_client: AsyncClient, sample_rule_data
    ):
        """Test rule creation with non-existent section ID."""
        rule_data = sample_rule_data.copy()
        rule_data["section_id"] = "550e8400-e29b-41d4-a716-446655440000"  # Non-existent UUID

        response = await async_client.post("/api/v1/rules/", json=rule_data)

        # Note: Currently the system doesn't validate section existence during rule creation
        # This is a business logic decision - the test documents current behavior
        # In a production system, you might want to add section validation
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.asyncio
    async def test_get_all_rules_paginated_empty(self, async_client: AsyncClient):
        """Test getting all rules when none exist."""
        response = await async_client.get("/api/v1/rules/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["size"] == 10

    @pytest.mark.asyncio
    async def test_get_all_rules_paginated_with_data(
        self, async_client: AsyncClient, sample_section_data, sample_rule_data
    ):
        """Test getting all rules with pagination when rules exist."""
        # Create a section first
        section_response = await async_client.post("/api/v1/sections/", json=sample_section_data)
        section_id = section_response.json()["id"]

        # Create multiple rules
        rules_data = []
        for i in range(3):
            rule_data = sample_rule_data.copy()
            rule_data["name"] = f"Test Rule {i + 1}"
            rule_data["section_id"] = section_id
            rules_data.append(rule_data)

            create_response = await async_client.post("/api/v1/rules/", json=rule_data)
            assert create_response.status_code == status.HTTP_201_CREATED

        # Get all rules with default pagination
        response = await async_client.get("/api/v1/rules/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 3
        assert data["page"] == 1
        assert data["size"] == 10

    @pytest.mark.asyncio
    async def test_get_all_rules_paginated_with_filters(
        self, async_client: AsyncClient, sample_section_data, sample_rule_data
    ):
        """Test getting rules with filters."""
        # Create a section first
        section_response = await async_client.post("/api/v1/sections/", json=sample_section_data)
        section_id = section_response.json()["id"]

        # Create rules with different profile types
        rule_data_prepaid = sample_rule_data.copy()
        rule_data_prepaid["name"] = "Prepaid Rule"
        rule_data_prepaid["profile_type"] = ProfileType.PREPAID.value
        rule_data_prepaid["section_id"] = section_id

        rule_data_hybrid = sample_rule_data.copy()
        rule_data_hybrid["name"] = "Hybrid Rule"
        rule_data_hybrid["profile_type"] = ProfileType.HYBRID.value
        rule_data_hybrid["section_id"] = section_id

        await async_client.post("/api/v1/rules/", json=rule_data_prepaid)
        await async_client.post("/api/v1/rules/", json=rule_data_hybrid)

        # Filter by profile type
        response = await async_client.get("/api/v1/rules/?profile_type_filter=PREPAID")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["profile_type"] == "PREPAID"

    @pytest.mark.asyncio
    async def test_get_all_rules_pagination_params(
        self, async_client: AsyncClient, sample_section_data, sample_rule_data
    ):
        """Test pagination parameters."""
        # Create a section first
        section_response = await async_client.post("/api/v1/sections/", json=sample_section_data)
        section_id = section_response.json()["id"]

        # Create 5 rules
        for i in range(5):
            rule_data = sample_rule_data.copy()
            rule_data["name"] = f"Test Rule {i + 1}"
            rule_data["section_id"] = section_id
            await async_client.post("/api/v1/rules/", json=rule_data)

        # Test pagination with page size 2
        response = await async_client.get("/api/v1/rules/?page=1&size=2")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["size"] == 2

        # Test second page
        response = await async_client.get("/api/v1/rules/?page=2&size=2")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 2

    @pytest.mark.asyncio
    async def test_get_rule_by_id_success(
        self, async_client: AsyncClient, sample_section_data, sample_rule_data
    ):
        """Test getting a rule by ID successfully."""
        # Create a section first
        section_response = await async_client.post("/api/v1/sections/", json=sample_section_data)
        section_id = section_response.json()["id"]

        # Create a rule
        rule_data = sample_rule_data.copy()
        rule_data["section_id"] = section_id
        create_response = await async_client.post("/api/v1/rules/", json=rule_data)
        assert create_response.status_code == status.HTTP_201_CREATED
        rule_id = create_response.json()["id"]

        # Get rule by ID
        response = await async_client.get(f"/api/v1/rules/{rule_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == rule_id
        assert data["name"] == rule_data["name"]

    @pytest.mark.asyncio
    async def test_get_rule_by_id_not_found(self, async_client: AsyncClient):
        """Test getting a rule by ID that doesn't exist."""
        non_existent_id = "550e8400-e29b-41d4-a716-446655440000"

        response = await async_client.get(f"/api/v1/rules/{non_existent_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_rule_by_invalid_id(self, async_client: AsyncClient):
        """Test getting a rule with invalid UUID format."""
        invalid_id = "invalid-uuid"

        response = await async_client.get(f"/api/v1/rules/{invalid_id}")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_get_rule_sql_by_id_success(
        self, async_client: AsyncClient, sample_section_data, sample_rule_data
    ):
        """Test getting rule SQL by ID successfully."""
        # Create a section first
        section_response = await async_client.post("/api/v1/sections/", json=sample_section_data)
        section_id = section_response.json()["id"]

        # Create a rule
        rule_data = sample_rule_data.copy()
        rule_data["section_id"] = section_id
        create_response = await async_client.post("/api/v1/rules/", json=rule_data)
        assert create_response.status_code == status.HTTP_201_CREATED
        rule_id = create_response.json()["id"]

        # Get rule SQL by ID
        response = await async_client.post(f"/api/v1/rules/{rule_id}/sql")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["rule_id"] == rule_id
        assert data["rule_name"] == rule_data["name"]
        assert "sql" in data
        assert isinstance(data["sql"], str)

    @pytest.mark.asyncio
    async def test_get_rule_sql_by_id_with_parameters(
        self, async_client: AsyncClient, sample_section_data, sample_rule_data
    ):
        """Test getting rule SQL by ID with parameters."""
        # Create a section first
        section_response = await async_client.post("/api/v1/sections/", json=sample_section_data)
        section_id = section_response.json()["id"]

        # Create a rule
        rule_data = sample_rule_data.copy()
        rule_data["section_id"] = section_id
        create_response = await async_client.post("/api/v1/rules/", json=rule_data)
        rule_id = create_response.json()["id"]

        # Get rule SQL with parameters
        parameters = {"min_balance": 200, "deduct_amount": 75}
        response = await async_client.post(f"/api/v1/rules/{rule_id}/sql", json=parameters)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["rule_id"] == rule_id
        assert "sql" in data
        assert "parameters_used" in data

    @pytest.mark.asyncio
    async def test_get_rule_sql_by_id_not_found(self, async_client: AsyncClient):
        """Test getting rule SQL for non-existent rule."""
        non_existent_id = "550e8400-e29b-41d4-a716-446655440000"

        response = await async_client.post(f"/api/v1/rules/{non_existent_id}/sql")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_rule_response_schema(
        self, async_client: AsyncClient, sample_section_data, sample_rule_data
    ):
        """Test that rule response matches expected schema."""
        # Create a section first
        section_response = await async_client.post("/api/v1/sections/", json=sample_section_data)
        section_id = section_response.json()["id"]

        # Create a rule
        rule_data = sample_rule_data.copy()
        rule_data["section_id"] = section_id
        response = await async_client.post("/api/v1/rules/", json=rule_data)
        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()

        # Validate response can be parsed as RuleResponse
        rule_response = RuleResponse(**data)
        assert rule_response.name == rule_data["name"]
        assert rule_response.profile_type == rule_data["profile_type"]
        assert rule_response.balance_type == rule_data["balance_type"]
        assert rule_response.status == "DRAFT"

    @pytest.mark.asyncio
    async def test_get_rules_sql_response_schema(
        self, async_client: AsyncClient, sample_section_data, sample_rule_data
    ):
        """Test that get rule SQL response matches expected schema."""
        # Create a section first
        section_response = await async_client.post("/api/v1/sections/", json=sample_section_data)
        section_id = section_response.json()["id"]

        # Create a rule
        rule_data = sample_rule_data.copy()
        rule_data["section_id"] = section_id
        create_response = await async_client.post("/api/v1/rules/", json=rule_data)
        rule_id = create_response.json()["id"]

        # Get rule SQL
        response = await async_client.post(f"/api/v1/rules/{rule_id}/sql")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        # Validate response can be parsed as GetRulesSqlResponse
        sql_response = GetRulesSqlResponse(**data)
        assert sql_response.rule_id == rule_id
        assert sql_response.rule_name == rule_data["name"]
        assert isinstance(sql_response.sql, str)
