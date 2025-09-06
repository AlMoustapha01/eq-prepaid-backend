# Repository Pattern Implementation with Raw SQL

This module provides a complete repository pattern implementation using raw SQL queries for maximum flexibility and performance. It includes ports, repositories, and mappers for clean architecture and separation of concerns.

## Architecture Overview

The repository pattern consists of three main components:

1. **BaseRepositoryPort** - Interface defining repository operations
2. **BaseRepository** - Raw SQL implementation of the repository for flexibility
3. **BaseMapper** - Converts between domain, persistence, and response models

## Key Benefits of Raw SQL Approach

✅ **Maximum Flexibility** - Write complex queries without ORM limitations
✅ **Better Performance** - Direct SQL execution without ORM overhead
✅ **Full Control** - Complete control over SQL generation and execution
✅ **Database-Specific Features** - Use PostgreSQL-specific features and optimizations
✅ **Easier Debugging** - See exact SQL queries being executed
✅ **Batch Operations** - Efficient batch inserts and updates

## Components

### BaseRepositoryPort (Interface)

Defines the contract for repository operations:

```python
from core.db import BaseRepositoryPort

class UserRepositoryPort(BaseRepositoryPort[User, UserModel, UserResponse, UUID]):
    # Interface is automatically implemented
    pass
```

### BaseMapper

Handles conversions between different model types:

```python
from core.db import BaseMapper

class UserMapper(BaseMapper[User, UserModel, UserResponse]):
    def to_domain(self, persistence_model: UserModel) -> User:
        return User(
            id=persistence_model.id,
            name=persistence_model.name,
            email=persistence_model.email
        )

    def to_persistence(self, domain_entity: User) -> UserModel:
        return UserModel(
            name=domain_entity.name,
            email=domain_entity.email
        )

    def to_response(self, domain_entity: User) -> UserResponse:
        return UserResponse(
            id=str(domain_entity.id),
            name=domain_entity.name,
            email=domain_entity.email
        )
```

### BaseRepository

SQLAlchemy implementation with full CRUD operations:

```python
from core.db import BaseRepository

class UserRepository(BaseRepository[User, UserModel, UserResponse, UUID]):
    def __init__(self, session):
        super().__init__(session, UserModel, UserMapper(), "users")
```

**Note:** The constructor now requires a `table_name` parameter for raw SQL queries.

## Available Operations

### Insert Operations

**Insert Single Entity:**
```python
user = User(name="John Doe", email="john@example.com")
created_user = await user_repo.insert_one(user)
```

**Insert Multiple Entities:**
```python
users = [
    User(name="Alice", email="alice@example.com"),
    User(name="Bob", email="bob@example.com")
]
created_users = await user_repo.insert_many(users)
```

### Find Operations

**Find by ID:**
```python
user = await user_repo.find_by_id(user_id)
if user:
    print(f"Found: {user.name}")
```

**Find All with Pagination:**
```python
from core.db import PaginationParams

pagination = PaginationParams(page=1, size=10)
result = await user_repo.find_all_paginated(pagination)

print(f"Found {len(result.items)} users")
print(f"Page {result.page} of {result.total_pages}")
print(f"Total: {result.total}")
```

**Find with Filters:**
```python
filters = {
    "age": {"gte": 18, "lte": 65},
    "name": {"like": "%John%"},
    "email": {"in": ["john@example.com", "jane@example.com"]}
}
result = await user_repo.find_all_paginated(pagination, filters)
```

### Update Operations

```python
user.name = "Updated Name"
updated_user = await user_repo.update(user)
```

### Delete Operations

```python
deleted = await user_repo.delete_by_id(user_id)
print(f"Deleted: {deleted}")
```

### Utility Operations

**Check Existence:**
```python
exists = await user_repo.exists_by_id(user_id)
```

**Count Records:**
```python
total = await user_repo.count()
filtered_count = await user_repo.count({"age": {"gte": 18}})
```

## Pagination

### PaginationParams

```python
from core.db import PaginationParams

# Basic pagination
pagination = PaginationParams(page=1, size=10)

# Validation is automatic
# page must be >= 1
# size must be >= 1 and <= 100
```

### PaginatedResult

```python
result = await repo.find_all_paginated(pagination)

# Access result data
items = result.items           # List of domain entities
total = result.total          # Total count
page = result.page            # Current page
size = result.size            # Page size

# Navigation helpers
has_next = result.has_next         # Boolean
has_previous = result.has_previous # Boolean
next_page = result.next_page       # Next page number or None
previous_page = result.previous_page # Previous page number or None
total_pages = result.total_pages   # Total number of pages
```

## Advanced Filtering

The repository supports complex filtering with operators:

```python
filters = {
    "field_name": "simple_value",           # Equality
    "age": {"gte": 18},                     # Greater than or equal
    "price": {"lt": 100},                   # Less than
    "status": {"in": ["active", "pending"]}, # In list
    "name": {"like": "%search%"},           # SQL LIKE
    "email": {"ilike": "%SEARCH%"},         # Case-insensitive LIKE
}
```

### Available Filter Operators

- `eq` - Equal to
- `ne` - Not equal to
- `gt` - Greater than
- `gte` - Greater than or equal
- `lt` - Less than
- `lte` - Less than or equal
- `in` - In list
- `not_in` - Not in list
- `like` - SQL LIKE pattern
- `ilike` - Case-insensitive LIKE pattern

## Complete Example

```python
from dataclasses import dataclass
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer

from core.db import (
    Base, UUIDTimestampMixin, BaseRepository, BaseMapper,
    PaginationParams, get_session_context
)

# Domain Entity
@dataclass
class User:
    id: Optional[UUID] = None
    name: str = ""
    email: str = ""
    age: Optional[int] = None

# Response DTO
@dataclass
class UserResponse:
    id: str
    name: str
    email: str
    age: Optional[int]

# Persistence Model
class UserModel(Base, UUIDTimestampMixin):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    age: Mapped[Optional[int]] = mapped_column(Integer)

# Mapper
class UserMapper(BaseMapper[User, UserModel, UserResponse]):
    def to_domain(self, persistence_model: UserModel) -> User:
        return User(
            id=persistence_model.id,
            name=persistence_model.name,
            email=persistence_model.email,
            age=persistence_model.age
        )

    def to_persistence(self, domain_entity: User) -> UserModel:
        model = UserModel(
            name=domain_entity.name,
            email=domain_entity.email,
            age=domain_entity.age
        )
        if domain_entity.id:
            model.id = domain_entity.id
        return model

    def to_response(self, domain_entity: User) -> UserResponse:
        return UserResponse(
            id=str(domain_entity.id),
            name=domain_entity.name,
            email=domain_entity.email,
            age=domain_entity.age
        )

# Repository
class UserRepository(BaseRepository[User, UserModel, UserResponse, UUID]):
    def __init__(self, session):
        super().__init__(session, UserModel, UserMapper(), "users")

# Usage
async def example_usage():
    async with get_session_context() as session:
        repo = UserRepository(session)

        # Create user
        user = User(name="John Doe", email="john@example.com", age=30)
        created = await repo.insert_one(user)

        # Find with pagination
        pagination = PaginationParams(page=1, size=10)
        result = await repo.find_all_paginated(pagination)

        # Convert to response
        mapper = UserMapper()
        responses = mapper.to_response_list(result.items)
```

## Raw SQL Query Examples

The repository generates optimized SQL queries:

**Insert Query:**
```sql
INSERT INTO users (name, email, age, created_at, updated_at)
VALUES (:name, :email, :age, :created_at, :updated_at)
RETURNING *
```

**Find by ID:**
```sql
SELECT * FROM users WHERE id = :entity_id
```

**Paginated Query with Filters:**
```sql
SELECT * FROM users
WHERE age >= :param_0 AND name LIKE :param_1
ORDER BY id
LIMIT :limit OFFSET :offset
```

**Count with Filters:**
```sql
SELECT COUNT(*) FROM users
WHERE age >= :param_0 AND name LIKE :param_1
```

## Best Practices

1. **Separation of Concerns**: Keep domain entities, persistence models, and response DTOs separate
2. **Type Safety**: Use generic types for compile-time type checking
3. **Error Handling**: Repository methods handle SQLAlchemy errors automatically
4. **Transaction Management**: Use session context managers for proper transaction handling
5. **Pagination**: Always use pagination for list operations to avoid performance issues
6. **Filtering**: Use the built-in filtering system for complex queries
7. **Mapping**: Implement all three mapper methods (to_domain, to_persistence, to_response)

## Custom Repository Extensions

You can extend the base repository for custom raw SQL operations:

```python
class UserRepository(BaseRepository[User, UserModel, UserResponse, UUID]):
    def __init__(self, session):
        super().__init__(session, UserModel, UserMapper(), "users")

    async def find_by_email(self, email: str) -> Optional[User]:
        """Custom method to find user by email using raw SQL."""
        query = "SELECT * FROM users WHERE email = :email"
        result = await self.session.execute(text(query), {"email": email})
        row = result.fetchone()

        if row is None:
            return None

        model_dict = dict(row._mapping)
        model = UserModel(**model_dict)
        return self.mapper.to_domain(model)

    async def find_adults(self, pagination: PaginationParams) -> PaginatedResult[User]:
        """Find users who are adults (age >= 18)."""
        filters = {"age": {"gte": 18}}
        return await self.find_all_paginated(pagination, filters)

    async def get_user_statistics(self) -> dict:
        """Get user statistics using complex raw SQL."""
        query = """
        SELECT
            COUNT(*) as total_users,
            AVG(age) as average_age,
            MIN(age) as youngest_age,
            MAX(age) as oldest_age,
            COUNT(CASE WHEN age >= 18 THEN 1 END) as adults
        FROM users
        """
        result = await self.session.execute(text(query))
        row = result.fetchone()
        return dict(row._mapping) if row else {}
```

## Advanced Raw SQL Features

### Complex Joins
```python
async def find_users_with_orders(self) -> List[dict]:
    """Example of complex JOIN query."""
    query = """
    SELECT u.*, COUNT(o.id) as order_count
    FROM users u
    LEFT JOIN orders o ON u.id = o.user_id
    GROUP BY u.id
    HAVING COUNT(o.id) > 0
    ORDER BY order_count DESC
    """
    result = await self.session.execute(text(query))
    return [dict(row._mapping) for row in result.fetchall()]
```

### Window Functions
```python
async def get_user_rankings(self) -> List[dict]:
    """Example using PostgreSQL window functions."""
    query = """
    SELECT
        id, name, age,
        ROW_NUMBER() OVER (ORDER BY age DESC) as age_rank,
        PERCENT_RANK() OVER (ORDER BY age) as age_percentile
    FROM users
    ORDER BY age_rank
    """
    result = await self.session.execute(text(query))
    return [dict(row._mapping) for row in result.fetchall()]
```

### Bulk Operations
```python
async def bulk_update_ages(self, age_updates: List[dict]) -> int:
    """Bulk update using raw SQL."""
    query = """
    UPDATE users
    SET age = :new_age, updated_at = NOW()
    WHERE id = :user_id
    """
    result = await self.session.execute(text(query), age_updates)
    return result.rowcount
```

This repository pattern provides a clean, type-safe, and maintainable way to handle database operations while maintaining separation between domain logic and persistence concerns.
