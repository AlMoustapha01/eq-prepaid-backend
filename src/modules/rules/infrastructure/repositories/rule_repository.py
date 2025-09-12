"""Rule repository implementation."""

import logging
from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import BaseRepository, BaseRepositoryPort
from modules.rules.domain.models.rule import RuleEntity
from modules.rules.domain.value_objects.enums import BalanceType, ProfileType, RuleStatus
from modules.rules.infrastructure.mappers.rule_mapper import RuleMapper
from modules.rules.infrastructure.models.rule_model import RuleModel

logger = logging.getLogger(__name__)


class RuleRepositoryPort(BaseRepositoryPort[RuleEntity, RuleModel, dict, UUID], ABC):
    """Rule repository port interface."""

    @abstractmethod
    async def find_by_section_id(self, section_id: UUID) -> list[RuleEntity]:
        """Find all rules by section ID."""

    @abstractmethod
    async def find_by_status(self, status: RuleStatus) -> list[RuleEntity]:
        """Find all rules by status."""

    @abstractmethod
    async def find_by_profile_type(self, profile_type: ProfileType) -> list[RuleEntity]:
        """Find all rules by profile type."""

    @abstractmethod
    async def find_by_balance_type(self, balance_type: BalanceType) -> list[RuleEntity]:
        """Find all rules by balance type."""

    @abstractmethod
    async def find_by_name(self, name: str) -> RuleEntity | None:
        """Find rule by name."""

    @abstractmethod
    async def exists_by_name(self, name: str) -> bool:
        """Check if rule exists by name."""


class RuleRepository(BaseRepository[RuleEntity, RuleModel, dict, UUID], RuleRepositoryPort):
    """Rule repository implementation using raw SQL."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, RuleModel, RuleMapper(), "rules")

    async def find_by_section_id(self, section_id: UUID) -> list[RuleEntity]:
        """Find all rules by section ID using raw SQL."""
        try:
            query = "SELECT * FROM rules WHERE section_id = :section_id ORDER BY created_at DESC"
            result = await self.session.execute(text(query), {"section_id": section_id})
            rows = result.fetchall()

            # Convert rows to model instances
            models = []
            for row in rows:
                model_dict = row._asdict()
                model = RuleModel(**model_dict)
                models.append(model)

            # Convert to domain entities
            return self.mapper.to_domain_list(models)

        except Exception:
            logger.exception("Error finding rules by section_id %s", section_id)
            raise

    async def find_by_status(self, status: RuleStatus) -> list[RuleEntity]:
        """Find all rules by status using raw SQL."""
        try:
            query = "SELECT * FROM rules WHERE status = :status ORDER BY created_at DESC"
            result = await self.session.execute(text(query), {"status": status.value})
            rows = result.fetchall()

            # Convert rows to model instances
            models = []
            for row in rows:
                model_dict = row._asdict()
                model = RuleModel(**model_dict)
                models.append(model)

            # Convert to domain entities
            return self.mapper.to_domain_list(models)

        except Exception:
            logger.exception("Error finding rules by status %s", status)
            raise

    async def find_by_profile_type(self, profile_type: ProfileType) -> list[RuleEntity]:
        """Find all rules by profile type using raw SQL."""
        try:
            query = (
                "SELECT * FROM rules WHERE profile_type = :profile_type ORDER BY created_at DESC"
            )
            result = await self.session.execute(text(query), {"profile_type": profile_type.value})
            rows = result.fetchall()

            # Convert rows to model instances
            models = []
            for row in rows:
                model_dict = row._asdict()
                model = RuleModel(**model_dict)
                models.append(model)

            # Convert to domain entities
            return self.mapper.to_domain_list(models)

        except Exception:
            logger.exception("Error finding rules by profile_type %s", profile_type)
            raise

    async def find_by_balance_type(self, balance_type: BalanceType) -> list[RuleEntity]:
        """Find all rules by balance type using raw SQL."""
        try:
            query = (
                "SELECT * FROM rules WHERE balance_type = :balance_type ORDER BY created_at DESC"
            )
            result = await self.session.execute(text(query), {"balance_type": balance_type.value})
            rows = result.fetchall()

            # Convert rows to model instances
            models = []
            for row in rows:
                model_dict = row._asdict()
                model = RuleModel(**model_dict)
                models.append(model)

            # Convert to domain entities
            return self.mapper.to_domain_list(models)

        except Exception:
            logger.exception("Error finding rules by balance_type %s", balance_type)
            raise

    async def find_by_name(self, name: str) -> RuleEntity | None:
        """Find rule by name using raw SQL."""
        try:
            query = "SELECT * FROM rules WHERE name = :name"
            result = await self.session.execute(text(query), {"name": name})
            row = result.fetchone()

            if row is None:
                return None

            # Convert row to model instance
            model_dict = row._asdict()
            model = RuleModel(**model_dict)

            # Convert to domain entity
            return self.mapper.to_domain(model)

        except Exception:
            logger.exception("Error finding rule by name %s", name)
            raise

    async def exists_by_name(self, name: str) -> bool:
        """Check if rule exists by name using raw SQL."""
        try:
            query = "SELECT EXISTS(SELECT 1 FROM rules WHERE name = :name)"
            result = await self.session.execute(text(query), {"name": name})
            return result.scalar() or False

        except Exception:
            logger.exception("Error checking rule existence by name %s", name)
            raise
