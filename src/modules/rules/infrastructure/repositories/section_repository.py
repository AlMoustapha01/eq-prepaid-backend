"""Section repository implementation."""

import logging
from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import BaseRepository, BaseRepositoryPort
from modules.rules.domain.models.section import SectionEntity, SectionStatus
from src.modules.rules.infrastructure.mappers.section_mapper import SectionMapper
from src.modules.rules.infrastructure.models.section_model import SectionModel

logger = logging.getLogger(__name__)


class SectionRepositoryPort(BaseRepositoryPort[SectionEntity, SectionModel, dict, UUID], ABC):
    """Section repository port interface."""

    @abstractmethod
    async def find_by_status(self, status: SectionStatus) -> list[SectionEntity]:
        """Find all sections by status."""

    @abstractmethod
    async def find_by_slug(self, slug: str) -> SectionEntity | None:
        """Find section by slug."""

    @abstractmethod
    async def find_by_name(self, name: str) -> SectionEntity | None:
        """Find section by name."""

    @abstractmethod
    async def exists_by_slug(self, slug: str) -> bool:
        """Check if section exists by slug."""

    @abstractmethod
    async def exists_by_name(self, name: str) -> bool:
        """Check if section exists by name."""


class SectionRepository(
    BaseRepository[SectionEntity, SectionModel, dict, UUID], SectionRepositoryPort
):
    """Section repository implementation using raw SQL."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, SectionModel, SectionMapper(), "sections")

    async def find_by_status(self, status: SectionStatus) -> list[SectionEntity]:
        """Find all sections by status using raw SQL."""
        try:
            query = "SELECT * FROM sections WHERE status = :status ORDER BY created_at DESC"
            result = await self.session.execute(text(query), {"status": status.value})
            rows = result.fetchall()

            # Convert rows to model instances
            models = []
            for row in rows:
                model_dict = dict(row._mapping)
                model = SectionModel(**model_dict)
                models.append(model)

            # Convert to domain entities
            return self.mapper.to_domain_list(models)

        except Exception as e:
            logger.exception(f"Error finding sections by status {status}: {e}")
            raise

    async def find_by_slug(self, slug: str) -> SectionEntity | None:
        """Find section by slug using raw SQL."""
        try:
            query = "SELECT * FROM sections WHERE slug = :slug"
            result = await self.session.execute(text(query), {"slug": slug})
            row = result.fetchone()

            if row is None:
                return None

            # Convert row to model instance
            model_dict = dict(row._mapping)
            model = SectionModel(**model_dict)

            # Convert to domain entity
            return self.mapper.to_domain(model)

        except Exception as e:
            logger.exception(f"Error finding section by slug {slug}: {e}")
            raise

    async def find_by_name(self, name: str) -> SectionEntity | None:
        """Find section by name using raw SQL."""
        try:
            query = "SELECT * FROM sections WHERE name = :name"
            result = await self.session.execute(text(query), {"name": name})
            row = result.fetchone()

            if row is None:
                return None

            # Convert row to model instance
            model_dict = dict(row._mapping)
            model = SectionModel(**model_dict)

            # Convert to domain entity
            return self.mapper.to_domain(model)

        except Exception as e:
            logger.exception(f"Error finding section by name {name}: {e}")
            raise

    async def exists_by_slug(self, slug: str) -> bool:
        """Check if section exists by slug using raw SQL."""
        try:
            query = "SELECT EXISTS(SELECT 1 FROM sections WHERE slug = :slug)"
            result = await self.session.execute(text(query), {"slug": slug})
            return result.scalar() or False

        except Exception as e:
            logger.exception(f"Error checking section existence by slug {slug}: {e}")
            raise

    async def exists_by_name(self, name: str) -> bool:
        """Check if section exists by name using raw SQL."""
        try:
            query = "SELECT EXISTS(SELECT 1 FROM sections WHERE name = :name)"
            result = await self.session.execute(text(query), {"name": name})
            return result.scalar() or False

        except Exception as e:
            logger.exception(f"Error checking section existence by name {name}: {e}")
            raise
