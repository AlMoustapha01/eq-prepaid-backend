"""Base repository implementation with raw SQL queries for flexibility."""

import logging
from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import text
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
    """Base repository implementation with raw SQL queries for maximum flexibility."""

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
            table_name: Database table name for raw queries

        """
        self.session = session
        self.model_class = model_class
        self.mapper = mapper
        self.table_name = table_name

    def _get_column_names(self) -> list[str]:
        """Get column names from the model class."""
        return [column.name for column in self.model_class.__table__.columns]

    def _build_where_clause(self, filters: dict[str, Any] | None) -> tuple[str, dict[str, Any]]:
        """Build WHERE clause from filters."""
        if not filters:
            return "", {}

        conditions = []
        params = {}
        param_counter = 0

        for field, value in filters.items():
            if isinstance(value, dict):
                # Handle operator-based filters
                for operator, op_value in value.items():
                    param_name = f"param_{param_counter}"
                    param_counter += 1

                    if operator == "eq":
                        conditions.append(f"{field} = :{param_name}")
                        params[param_name] = op_value
                    elif operator == "ne":
                        conditions.append(f"{field} != :{param_name}")
                        params[param_name] = op_value
                    elif operator == "gt":
                        conditions.append(f"{field} > :{param_name}")
                        params[param_name] = op_value
                    elif operator == "gte":
                        conditions.append(f"{field} >= :{param_name}")
                        params[param_name] = op_value
                    elif operator == "lt":
                        conditions.append(f"{field} < :{param_name}")
                        params[param_name] = op_value
                    elif operator == "lte":
                        conditions.append(f"{field} <= :{param_name}")
                        params[param_name] = op_value
                    elif operator == "in":
                        if isinstance(op_value, (list, tuple)) and op_value:
                            placeholders = []
                            for item in op_value:
                                item_param = f"param_{param_counter}"
                                param_counter += 1
                                placeholders.append(f":{item_param}")
                                params[item_param] = item
                            conditions.append(f"{field} IN ({', '.join(placeholders)})")
                    elif operator == "not_in":
                        if isinstance(op_value, (list, tuple)) and op_value:
                            placeholders = []
                            for item in op_value:
                                item_param = f"param_{param_counter}"
                                param_counter += 1
                                placeholders.append(f":{item_param}")
                                params[item_param] = item
                            conditions.append(f"{field} NOT IN ({', '.join(placeholders)})")
                    elif operator == "like":
                        conditions.append(f"{field} LIKE :{param_name}")
                        params[param_name] = op_value
                    elif operator == "ilike":
                        conditions.append(f"{field} ILIKE :{param_name}")
                        params[param_name] = op_value
            else:
                # Handle simple equality
                param_name = f"param_{param_counter}"
                param_counter += 1
                conditions.append(f"{field} = :{param_name}")
                params[param_name] = value

        where_clause = " AND ".join(conditions) if conditions else ""
        return where_clause, params

    async def insert_one(self, entity: DomainT) -> DomainT:
        """Insert a single entity using raw SQL."""
        try:
            persistence_model = self.mapper.to_persistence(entity)

            # Get column names and values (excluding id if it's auto-generated)
            columns = [
                col.name
                for col in self.model_class.__table__.columns
                if not col.primary_key or getattr(persistence_model, col.name) is not None
            ]
            values = [getattr(persistence_model, col) for col in columns]

            # Build INSERT query
            placeholders = ", ".join([f":{col}" for col in columns])
            query = f"INSERT INTO {self.table_name} ({', '.join(columns)}) VALUES ({placeholders}) RETURNING *"

            # Execute query
            params = dict(zip(columns, values, strict=False))
            result = await self.session.execute(text(query), params)
            row = result.fetchone()

            if row is None:
                raise RuntimeError("Insert failed - no row returned")

            # Convert row to model instance
            model_dict = dict(row._mapping)
            new_model = self.model_class(**model_dict)

            domain_entity = self.mapper.to_domain(new_model)
            logger.debug(f"Inserted entity: {type(entity).__name__}")
            return domain_entity

        except SQLAlchemyError as e:
            logger.exception(f"Error inserting entity: {e}")
            await self.session.rollback()
            raise
        except Exception as e:
            logger.exception(f"Unexpected error inserting entity: {e}")
            await self.session.rollback()
            raise

    async def insert_many(self, entities: list[DomainT]) -> list[DomainT]:
        """Insert multiple entities using raw SQL batch insert."""
        if not entities:
            return []

        try:
            persistence_models = self.mapper.to_persistence_list(entities)

            # Get column names (excluding auto-generated primary keys)
            first_model = persistence_models[0]
            columns = [
                col.name
                for col in self.model_class.__table__.columns
                if not col.primary_key or getattr(first_model, col.name) is not None
            ]

            # Build batch INSERT query
            placeholders = ", ".join([f":{col}" for col in columns])
            query = f"INSERT INTO {self.table_name} ({', '.join(columns)}) VALUES ({placeholders}) RETURNING *"

            # Prepare batch parameters
            batch_params = []
            for model in persistence_models:
                params = {col: getattr(model, col) for col in columns}
                batch_params.append(params)

            # Execute batch insert
            result = await self.session.execute(text(query), batch_params)
            rows = result.fetchall()

            # Convert rows to model instances
            new_models = []
            for row in rows:
                model_dict = dict(row._mapping)
                new_model = self.model_class(**model_dict)
                new_models.append(new_model)

            domain_entities = self.mapper.to_domain_list(new_models)
            logger.debug(f"Inserted {len(entities)} entities: {type(entities[0]).__name__}")
            return domain_entities

        except SQLAlchemyError as e:
            logger.exception(f"Error inserting entities: {e}")
            await self.session.rollback()
            raise
        except Exception as e:
            logger.exception(f"Unexpected error inserting entities: {e}")
            await self.session.rollback()
            raise

    async def find_by_id(self, entity_id: IdT) -> DomainT | None:
        """Find entity by ID using raw SQL."""
        try:
            query = f"SELECT * FROM {self.table_name} WHERE id = :entity_id"
            result = await self.session.execute(text(query), {"entity_id": entity_id})
            row = result.fetchone()

            if row is None:
                logger.debug(f"Entity not found with ID: {entity_id}")
                return None

            # Convert row to model instance
            model_dict = dict(row._mapping)
            persistence_model = self.model_class(**model_dict)

            domain_entity = self.mapper.to_domain(persistence_model)
            logger.debug(f"Found entity with ID: {entity_id}")
            return domain_entity

        except SQLAlchemyError as e:
            logger.exception(f"Error finding entity by ID {entity_id}: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error finding entity by ID {entity_id}: {e}")
            raise

    async def find_all_paginated(
        self, pagination: PaginationParams, filters: dict | None = None
    ) -> PaginatedResult[DomainT]:
        """Find all entities with pagination using raw SQL."""
        try:
            # Build WHERE clause
            where_clause, params = self._build_where_clause(filters)
            where_sql = f"WHERE {where_clause}" if where_clause else ""

            # Get total count
            count_query = f"SELECT COUNT(*) FROM {self.table_name} {where_sql}"
            count_result = await self.session.execute(text(count_query), params)
            total = count_result.scalar() or 0

            # Build main query with pagination
            query = f"SELECT * FROM {self.table_name} {where_sql} ORDER BY id LIMIT :limit OFFSET :offset"
            query_params = {**params, "limit": pagination.limit, "offset": pagination.offset}

            # Execute query
            result = await self.session.execute(text(query), query_params)
            rows = result.fetchall()

            # Convert rows to model instances
            persistence_models = []
            for row in rows:
                model_dict = dict(row._mapping)
                model = self.model_class(**model_dict)
                persistence_models.append(model)

            # Convert to domain entities
            domain_entities = self.mapper.to_domain_list(persistence_models)

            logger.debug(f"Found {len(domain_entities)} entities with pagination")

            return PaginatedResult(
                items=domain_entities, total=total, page=pagination.page, size=pagination.size
            )

        except SQLAlchemyError as e:
            logger.exception(f"Error finding entities with pagination: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error finding entities with pagination: {e}")
            raise

    async def delete_by_id(self, entity_id: IdT) -> bool:
        """Delete entity by ID using raw SQL."""
        try:
            query = f"DELETE FROM {self.table_name} WHERE id = :entity_id"
            result = await self.session.execute(text(query), {"entity_id": entity_id})

            deleted = result.rowcount > 0
            if deleted:
                logger.debug(f"Deleted entity with ID: {entity_id}")
            else:
                logger.debug(f"No entity found to delete with ID: {entity_id}")

            return deleted

        except SQLAlchemyError as e:
            logger.exception(f"Error deleting entity by ID {entity_id}: {e}")
            await self.session.rollback()
            raise
        except Exception as e:
            logger.exception(f"Unexpected error deleting entity by ID {entity_id}: {e}")
            await self.session.rollback()
            raise

    async def update(self, entity: DomainT) -> DomainT:
        """Update an existing entity using raw SQL."""
        try:
            persistence_model = self.mapper.to_persistence(entity)

            # Get all columns except id
            update_columns = [
                col.name for col in self.model_class.__table__.columns if col.name != "id"
            ]

            # Build UPDATE query
            set_clauses = [f"{col} = :{col}" for col in update_columns]
            query = (
                f"UPDATE {self.table_name} SET {', '.join(set_clauses)} WHERE id = :id RETURNING *"
            )

            # Prepare parameters
            params = {col: getattr(persistence_model, col) for col in update_columns}
            params["id"] = persistence_model.id

            # Execute update
            result = await self.session.execute(text(query), params)
            row = result.fetchone()

            if row is None:
                msg = f"Entity with ID {persistence_model.id} not found"
                raise ValueError(msg)

            # Convert row to model instance
            model_dict = dict(row._mapping)
            updated_model = self.model_class(**model_dict)

            domain_entity = self.mapper.to_domain(updated_model)
            logger.debug(f"Updated entity with ID: {persistence_model.id}")
            return domain_entity

        except SQLAlchemyError as e:
            logger.exception(f"Error updating entity: {e}")
            await self.session.rollback()
            raise
        except Exception as e:
            logger.exception(f"Unexpected error updating entity: {e}")
            await self.session.rollback()
            raise

    async def exists_by_id(self, entity_id: IdT) -> bool:
        """Check if entity exists by ID using raw SQL."""
        try:
            query = f"SELECT EXISTS(SELECT 1 FROM {self.table_name} WHERE id = :entity_id)"
            result = await self.session.execute(text(query), {"entity_id": entity_id})
            exists = result.scalar() or False

            logger.debug(f"Entity exists check for ID {entity_id}: {exists}")
            return exists

        except SQLAlchemyError as e:
            logger.exception(f"Error checking entity existence by ID {entity_id}: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error checking entity existence by ID {entity_id}: {e}")
            raise

    async def count(self, filters: dict | None = None) -> int:
        """Count entities with optional filters using raw SQL."""
        try:
            # Build WHERE clause
            where_clause, params = self._build_where_clause(filters)
            where_sql = f"WHERE {where_clause}" if where_clause else ""

            # Build and execute count query
            query = f"SELECT COUNT(*) FROM {self.table_name} {where_sql}"
            result = await self.session.execute(text(query), params)
            count = result.scalar() or 0

            logger.debug(f"Entity count: {count}")
            return count

        except SQLAlchemyError as e:
            logger.exception(f"Error counting entities: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error counting entities: {e}")
            raise

    def _build_filter_conditions(self, filters: dict) -> Any | None:
        """
        Legacy method - kept for backward compatibility.
        Use _build_where_clause instead for raw SQL queries.

        Args:
            filters: Dictionary of filter criteria

        Returns:
            SQLAlchemy filter conditions or None

        """
        conditions = []

        for field_name, value in filters.items():
            if hasattr(self.model_class, field_name):
                field = getattr(self.model_class, field_name)

                if isinstance(value, dict):
                    # Handle complex filters like {"gt": 10}, {"in": [1, 2, 3]}
                    for operator, operand in value.items():
                        if operator == "eq":
                            conditions.append(field == operand)
                        elif operator == "ne":
                            conditions.append(field != operand)
                        elif operator == "gt":
                            conditions.append(field > operand)
                        elif operator == "gte":
                            conditions.append(field >= operand)
                        elif operator == "lt":
                            conditions.append(field < operand)
                        elif operator == "lte":
                            conditions.append(field <= operand)
                        elif operator == "in":
                            conditions.append(field.in_(operand))
                        elif operator == "not_in":
                            conditions.append(~field.in_(operand))
                        elif operator == "like":
                            conditions.append(field.like(operand))
                        elif operator == "ilike":
                            conditions.append(field.ilike(operand))
                else:
                    # Simple equality filter
                    conditions.append(field == value)

        if not conditions:
            return None

        # Combine all conditions with AND
        from sqlalchemy import and_

        return and_(*conditions) if len(conditions) > 1 else conditions[0]
