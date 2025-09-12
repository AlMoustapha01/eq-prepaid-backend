"""Test configuration and fixtures for end-to-end tests."""

import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app import app
from core.db.base import Base
from core.db.session import get_async_session
from modules.rules.api.dependencies import get_rule_repository, get_section_repository
from modules.rules.domain.value_objects.enums import BalanceType, ProfileType

# Import models to ensure they are registered with Base metadata
from modules.rules.infrastructure.models.rule_model import RuleModel  # noqa: F401
from modules.rules.infrastructure.models.section_model import SectionModel  # noqa: F401
from modules.rules.infrastructure.repositories.rule_repository import RuleRepository
from modules.rules.infrastructure.repositories.section_repository import SectionRepository

# Set test environment variables
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["DEBUG"] = "true"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False, future=True)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Clean up
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client(test_session) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for the FastAPI app with test database."""

    # Override database dependencies
    async def get_test_session() -> AsyncSession:
        return test_session

    async def get_test_rule_repository() -> RuleRepository:
        return RuleRepository(test_session)

    async def get_test_section_repository() -> SectionRepository:
        return SectionRepository(test_session)

    app.dependency_overrides[get_async_session] = get_test_session
    app.dependency_overrides[get_rule_repository] = get_test_rule_repository
    app.dependency_overrides[get_section_repository] = get_test_section_repository

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"host": "localhost"},
    ) as ac:
        yield ac

    # Clean up overrides
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def setup_test_db(test_engine):
    """Set up and tear down test database for each test."""
    # Create tables fresh for each test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Clean up after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def sample_section_data():
    """Sample section data for testing."""
    return {"name": "Test Section", "description": "A test section for unit testing"}


@pytest.fixture
def sample_rule_data():
    """Sample rule data for testing."""
    return {
        "name": "Test Rule",
        "profile_type": ProfileType.PREPAID.value,
        "balance_type": BalanceType.MAIN_BALANCE.value,
        "database_table_name": ["test_table"],
        "config": {
            "select": {
                "fields": [{"name": "balance", "expression": "balance", "alias": None}],
                "aggregations": [],
            },
            "from": {"main_table": "test_table", "alias": None},
            "joins": [],
            "conditions": {
                "where": [
                    {"field": "balance", "operator": ">=", "value": 100, "logical_operator": None}
                ]
            },
            "group_by": [],
            "having": [],
            "order_by": [],
            "parameters": {},
        },
    }


@pytest.fixture
def sample_rule_data_with_section_id(sample_rule_data):
    """Sample rule data with a section ID for testing."""
    data = sample_rule_data.copy()
    data["section_id"] = str(uuid4())
    return data
