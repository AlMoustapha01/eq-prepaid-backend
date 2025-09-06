"""Example usage of the repository pattern."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.base import Base
from src.core.db.mixins import UUIDTimestampMixin

from .base_mapper import BaseMapper
from .base_repository import BaseRepository
from .pagination import PaginationParams


# Domain Entity
@dataclass
class User:
    """User domain entity."""

    id: uuid.UUID | None = None
    name: str = ""
    email: str = ""
    age: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# Response DTO
@dataclass
class UserResponse:
    """User response DTO."""

    id: str
    name: str
    email: str
    age: int | None
    created_at: str
    updated_at: str | None


# Persistence Model
class UserModel(Base, UUIDTimestampMixin):
    """User persistence model."""

    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)


# Mapper Implementation
class UserMapper(BaseMapper[User, UserModel, UserResponse]):
    """User mapper implementation."""

    def to_domain(self, persistence_model: UserModel) -> User:
        """Convert persistence model to domain entity."""
        return User(
            id=persistence_model.id,
            name=persistence_model.name,
            email=persistence_model.email,
            age=persistence_model.age,
            created_at=persistence_model.created_at,
            updated_at=persistence_model.updated_at,
        )

    def to_persistence(self, domain_entity: User) -> UserModel:
        """Convert domain entity to persistence model."""
        model = UserModel(name=domain_entity.name, email=domain_entity.email, age=domain_entity.age)
        if domain_entity.id:
            model.id = domain_entity.id
        return model

    def to_response(self, domain_entity: User) -> UserResponse:
        """Convert domain entity to response DTO."""
        return UserResponse(
            id=str(domain_entity.id),
            name=domain_entity.name,
            email=domain_entity.email,
            age=domain_entity.age,
            created_at=domain_entity.created_at.isoformat() if domain_entity.created_at else "",
            updated_at=domain_entity.updated_at.isoformat() if domain_entity.updated_at else None,
        )


# Repository Implementation
class UserRepository(BaseRepository[User, UserModel, UserResponse, uuid.UUID]):
    """User repository implementation."""

    def __init__(self, session):
        """Initialize user repository."""
        super().__init__(session, UserModel, UserMapper(), "users")


# Usage Examples
async def repository_usage_examples(session):
    """Examples of using the repository pattern."""
    # Initialize repository
    user_repo = UserRepository(session)

    # 1. Insert one user
    new_user = User(name="John Doe", email="john@example.com", age=30)
    created_user = await user_repo.insert_one(new_user)

    # 2. Insert many users
    users_to_create = [
        User(name="Alice Smith", email="alice@example.com", age=25),
        User(name="Bob Johnson", email="bob@example.com", age=35),
        User(name="Carol Brown", email="carol@example.com", age=28),
    ]
    created_users = await user_repo.insert_many(users_to_create)

    # 3. Find by ID
    user_id = created_user.id
    found_user = await user_repo.find_by_id(user_id)
    if found_user:
        pass

    # 4. Find all paginated
    pagination = PaginationParams(page=1, size=10)
    await user_repo.find_all_paginated(pagination)

    # 5. Find with filters
    filters = {"age": {"gte": 25, "lte": 35}}
    await user_repo.find_all_paginated(pagination, filters)

    # 6. Update user
    if found_user:
        found_user.age = 31
        updated_user = await user_repo.update(found_user)
        if updated_user:
            pass

    # 7. Check if exists
    await user_repo.exists_by_id(user_id)

    # 8. Count users
    await user_repo.count()

    # 9. Count with filters
    await user_repo.count({"age": {"gte": 18}})

    # 10. Delete user
    await user_repo.delete_by_id(user_id)

    # 11. Using mapper directly
    mapper = UserMapper()
    if created_users:
        mapper.to_response(created_users[0])


# Advanced filtering example
async def advanced_filtering_example(session):
    """Example of advanced filtering capabilities."""
    user_repo = UserRepository(session)
    pagination = PaginationParams(page=1, size=20)

    # Complex filters
    filters = {
        "age": {"gte": 18, "lte": 65},  # Age between 18 and 65
        "name": {"like": "%John%"},  # Name contains "John"
        # "email": {"in": ["john@example.com", "jane@example.com"]}  # Email in list
    }

    return await user_repo.find_all_paginated(pagination, filters)


# Repository factory pattern
class RepositoryFactory:
    """Factory for creating repositories."""

    def __init__(self, session):
        """Initialize factory with session."""
        self.session = session

    def create_user_repository(self) -> UserRepository:
        """Create user repository."""
        return UserRepository(self.session)

    # Add more repository creation methods as needed


if __name__ == "__main__":
    pass
