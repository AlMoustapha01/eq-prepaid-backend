"""Base repository implementation using SQLAlchemy ORM for type safety and maintainability."""

import logging
from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import and_, delete, func, insert, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from .base_mapper import BaseMapper
from .base_port import BaseRepositoryPort
from .pagination import PaginatedResult, PaginationParams

logger = logging.getLogger(__name__)

# Type variables
DomainT = TypeVar("DomainT")
PersistenceT = TypeVar("PersistenceT")
ResponseT = TypeVar("ResponseT")
IdT = TypeVar("IdT", UUID, str, int)


class BaseRepository(
    BaseRepositoryPort[DomainT, PersistenceT, ResponseT, IdT],
    Generic[DomainT, PersistenceT, ResponseT, IdT],
):
    """Base repository implementation using SQLAlchemy ORM for type safety and maintainability."""

    def __init__(
        self,
        session: AsyncSession,
        model_class: type[PersistenceT],
        mapper: BaseMapper[DomainT, PersistenceT, ResponseT],
        table_name: str,
    ):
        """
        Initialize base repository.

        Args:
            session: Async SQLAlchemy session
            model_class: SQLAlchemy model class
            mapper: Mapper for model conversions
            table_name: Database table name (kept for compatibility)

        """
        self.session = session
        self.model_class = model_class
        self.mapper = mapper
        self.table_name = table_name

    def _get_column_names(self) -> list[str]:
        """Get column names from the model class."""
        return [column.name for column in self.model_class.__table__.columns]

    async def insert_one(self, entity: DomainT) -> DomainT:
        """Insert a single entity using SQLAlchemy Core with RETURNING for performance."""
        try:
            persistence_model = self.mapper.to_persistence(entity)

            # Get only valid column values, excluding SQLAlchemy internals
            column_values = {
                col.name: getattr(persistence_model, col.name)
                for col in self.model_class.__table__.columns
                if not col.primary_key or getattr(persistence_model, col.name) is not None
            }

            stmt = insert(self.model_class).values(**column_values).returning(self.model_class)

            result = await self.session.execute(stmt)
            new_model = result.scalar_one()

            domain_entity = self.mapper.to_domain(new_model)

            logger.debug("Inserted entity: %s", type(entity).__name__)

        except SQLAlchemyError:
            logger.exception("Error inserting entity")
            await self.session.rollback()
            raise
        except Exception:
            logger.exception("Unexpected error inserting entity")
            await self.session.rollback()
            raise
        else:
            return domain_entity

    async def insert_many(self, entities: list[DomainT]) -> list[DomainT]:
        """Insert multiple entities using SQLAlchemy Core with RETURNING for performance."""
        if not entities:
            return []

        try:
            persistence_models = self.mapper.to_persistence_list(entities)

            # Prepare batch values, excluding SQLAlchemy internals
            batch_values = []
            for model in persistence_models:
                column_values = {
                    col.name: getattr(model, col.name)
                    for col in self.model_class.__table__.columns
                    if not col.primary_key or getattr(model, col.name) is not None
                }
                batch_values.append(column_values)

            # Use bulk insert with RETURNING for efficiency
            stmt = insert(self.model_class).returning(self.model_class)

            result = await self.session.execute(stmt, batch_values)
            new_models = result.scalars().all()

            domain_entities = self.mapper.to_domain_list(new_models)
            logger.debug("Inserted %s entities: %s", len(entities), type(entities[0]).__name__)

        except SQLAlchemyError:
            logger.exception("Error inserting entities")
            await self.session.rollback()
            raise
        except Exception:
            logger.exception("Unexpected error inserting entities")
            await self.session.rollback()
            raise
        else:
            return domain_entities

    async def find_by_id(self, entity_id: IdT) -> DomainT | None:
        """Find entity by ID using SQLAlchemy ORM."""
        try:
            stmt = select(self.model_class).where(self.model_class.id == entity_id)
            result = await self.session.execute(stmt)
            persistence_model = result.scalar_one_or_none()

            if persistence_model is None:
                logger.debug("Entity not found with ID: %s", entity_id)
                return None

            domain_entity = self.mapper.to_domain(persistence_model)
            logger.debug("Found entity with ID: %s", entity_id)

        except SQLAlchemyError:
            logger.exception("Error finding entity by ID %s", entity_id)
            raise
        except Exception:
            logger.exception("Unexpected error finding entity by ID %s", entity_id)
            raise
        else:
            return domain_entity

    async def find_all_paginated(
        self, pagination: PaginationParams, filters: dict | None = None
    ) -> PaginatedResult[DomainT]:
        """Find all entities with pagination using SQLAlchemy ORM."""
        try:
            # Build base query
            stmt = select(self.model_class)

            # Apply filters if provided
            if filters:
                filter_conditions = self._build_filter_conditions(filters)
                if filter_conditions is not None:
                    stmt = stmt.where(filter_conditions)

            # Get total count
            count_stmt = select(func.count()).select_from(stmt.subquery())
            count_result = await self.session.execute(count_stmt)
            total = count_result.scalar() or 0

            # Apply pagination
            stmt = (
                stmt.order_by(self.model_class.id).offset(pagination.offset).limit(pagination.limit)
            )

            # Execute query
            result = await self.session.execute(stmt)
            persistence_models = result.scalars().all()

            # Convert to domain entities
            domain_entities = self.mapper.to_domain_list(persistence_models)

            logger.debug("Found %s entities with pagination", len(domain_entities))

            return PaginatedResult(
                items=domain_entities, total=total, page=pagination.page, size=pagination.size
            )

        except SQLAlchemyError:
            logger.exception("Error finding entities with pagination")
            raise
        except Exception:
            logger.exception("Unexpected error finding entities with pagination")
            raise

    async def delete_by_id(self, entity_id: IdT) -> bool:
        """Delete entity by ID using SQLAlchemy ORM."""
        try:
            stmt = delete(self.model_class).where(self.model_class.id == entity_id)
            result = await self.session.execute(stmt)

            deleted = result.rowcount > 0
            if deleted:
                logger.debug("Deleted entity with ID: %s", entity_id)
            else:
                logger.debug("No entity found to delete with ID: %s", entity_id)

        except SQLAlchemyError:
            logger.exception("Error deleting entity by ID %s", entity_id)
            await self.session.rollback()
            raise
        except Exception:
            logger.exception("Unexpected error deleting entity by ID %s", entity_id)
            await self.session.rollback()
            raise
        else:
            return deleted

    async def update(self, entity: DomainT) -> DomainT:
        """Update an existing entity using SQLAlchemy ORM."""
        try:
            persistence_model = self.mapper.to_persistence(entity)

            # Merge the model with the session
            updated_model = await self.session.merge(persistence_model)
            await self.session.flush()
            await self.session.refresh(updated_model)

            domain_entity = self.mapper.to_domain(updated_model)
            logger.debug("Updated entity with ID: %s", persistence_model.id)

        except SQLAlchemyError:
            logger.exception("Error updating entity")
            await self.session.rollback()
            raise
        except Exception:
            logger.exception("Unexpected error updating entity")
            await self.session.rollback()
            raise
        else:
            return domain_entity

    async def exists_by_id(self, entity_id: IdT) -> bool:
        """Check if entity exists by ID using SQLAlchemy ORM."""
        try:
            stmt = select(func.count()).where(self.model_class.id == entity_id)
            result = await self.session.execute(stmt)
            count = result.scalar() or 0
            exists = count > 0

            logger.debug("Entity exists check for ID %s: %s", entity_id, exists)

        except SQLAlchemyError:
            logger.exception("Error checking entity existence by ID %s", entity_id)
            raise
        except Exception:
            logger.exception("Unexpected error checking entity existence by ID %s", entity_id)
            raise
        else:
            return exists

    async def count(self, filters: dict | None = None) -> int:
        """Count entities with optional filters using SQLAlchemy ORM."""
        try:
            # Build base query
            stmt = select(func.count()).select_from(self.model_class)
            # Apply filters if provided
            if filters:
                filter_conditions = self._build_filter_conditions(filters)
                if filter_conditions is not None:
                    stmt = stmt.where(filter_conditions)

            # Execute count query
            result = await self.session.execute(stmt)
            count = result.scalar() or 0

            logger.debug("Entity count: %s", count)

        except SQLAlchemyError:
            logger.exception("Error counting entities")
            raise
        except Exception:
            logger.exception("Unexpected error counting entities")
            raise
        else:
            return count

    def _apply_operator(self, field: Any, operator: str, operand: Any) -> Any:
        """Map operator to SQLAlchemy condition."""
        ops = {
            "eq": lambda f, v: f == v,
            "ne": lambda f, v: f != v,
            "gt": lambda f, v: f > v,
            "gte": lambda f, v: f >= v,
            "lt": lambda f, v: f < v,
            "lte": lambda f, v: f <= v,
            "in": lambda f, v: f.in_(v),
            "not_in": lambda f, v: ~f.in_(v),
            "like": lambda f, v: f.like(v),
            "ilike": lambda f, v: f.ilike(v),
        }
        return ops.get(operator, lambda _f, _v: None)(field, operand)

    def _build_filter_conditions(self, filters: dict) -> Any | None:
        """Build SQLAlchemy filter conditions from filters dictionary."""
        conditions = []

        for field_name, _value in filters.items():
            if not hasattr(self.model_class, field_name):
                continue

            field = getattr(self.model_class, field_name)
            value = _value

            if isinstance(value, dict):
                for operator, operand in value.items():
                    condition = self._apply_operator(field, operator, operand)
                    if condition is not None:
                        conditions.append(condition)
            else:
                conditions.append(field == value)

        if not conditions:
            return None

        return and_(*conditions) if len(conditions) > 1 else conditions[0]
