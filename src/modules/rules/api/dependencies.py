"""API dependencies for dependency injection."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_session_context
from modules.rules.infrastructure.repositories.rule_repository import RuleRepository
from modules.rules.infrastructure.repositories.section_repository import (
    SectionRepository,
)


async def get_session() -> AsyncSession:
    """Get database session."""
    async with get_session_context() as session:
        yield session


def get_section_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SectionRepository:
    """Get section repository instance."""
    return SectionRepository(session)


def get_rule_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RuleRepository:
    """Get rule repository instance."""
    return RuleRepository(session)
