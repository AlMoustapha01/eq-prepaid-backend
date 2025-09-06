# Async PostgreSQL Database Connection

This module provides async PostgreSQL database connectivity using SQLAlchemy and asyncpg for the EQ Prepaid Backend application.

## Features

- **Async Support**: Full async/await support using SQLAlchemy 2.0+ and asyncpg
- **Connection Management**: Robust connection pooling and lifecycle management
- **Session Factory**: Async session factory with proper transaction handling
- **Health Checks**: Built-in database health monitoring
- **Configuration**: Environment-based configuration with validation
- **Lifecycle Management**: Application startup/shutdown integration
- **Error Handling**: Comprehensive error handling and logging

## Quick Start

### 1. Environment Configuration

Create a `.env` file with your PostgreSQL credentials:

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_DB=your_database
```

### 2. Basic Usage

```python
import asyncio
from core.db import initialize_database, get_session_context

async def main():
    # Initialize database connections
    await initialize_database()

    # Use database session
    async with get_session_context() as session:
        result = await session.execute("SELECT 1")
        print(result.scalar())

asyncio.run(main())
```

### 3. FastAPI Integration

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import database_lifespan, get_async_session

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with database_lifespan():
        yield

app = FastAPI(lifespan=lifespan)

@app.get("/users")
async def get_users(session: AsyncSession = Depends(get_async_session)):
    # Use session for database operations
    pass
```

## Components

### DatabaseConfig
Manages database configuration and engine creation.

```python
from core.db import DatabaseConfig

config = DatabaseConfig()
engine = config.create_engine()
```

### DatabaseManager
Handles database connections and lifecycle.

```python
from core.db import get_database_manager

db_manager = await get_database_manager()
is_healthy = await db_manager.health_check()
```

### AsyncSessionFactory
Creates and manages async database sessions.

```python
from core.db import get_session_context

async with get_session_context() as session:
    # Your database operations here
    pass
```

## Database Models

### Base Model
All database models should inherit from the provided `Base` class:

```python
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from core.db import Base, UUIDTimestampMixin

class User(Base, UUIDTimestampMixin):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    # id (UUID), created_at, and updated_at are automatically added
```

### Available Mixins

#### UUID Mixins

**UUIDMixin** - Native UUID primary key (recommended):
```python
from core.db import Base, UUIDMixin

class Product(Base, UUIDMixin):
    __tablename__ = "products"

    name: Mapped[str] = mapped_column(String(200))
    # Adds: id: UUID (primary key)
```

**UUIDStringMixin** - String UUID primary key:
```python
from core.db import Base, UUIDStringMixin

class Category(Base, UUIDStringMixin):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(100))
    # Adds: id: str (36 characters, primary key)
```

**UUIDFieldMixin** - UUID field (not primary key):
```python
from core.db import Base, UUIDFieldMixin

class Order(Base, UUIDFieldMixin):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_number: Mapped[str] = mapped_column(String(50))
    # Adds: uuid: UUID (unique field)
```

#### Timestamp Mixin

**TimestampMixin** - Automatic timestamps:
```python
from core.db import Base, TimestampMixin

class MyModel(Base, TimestampMixin):
    __tablename__ = "my_table"

    name: Mapped[str] = mapped_column(String(100))
    # Adds: created_at: datetime, updated_at: datetime
```

#### Combined Mixins

**UUIDTimestampMixin** - UUID primary key + timestamps:
```python
from core.db import Base, UUIDTimestampMixin

class User(Base, UUIDTimestampMixin):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(100))
    # Adds: id: UUID, created_at: datetime, updated_at: datetime
```

**UUIDStringTimestampMixin** - String UUID primary key + timestamps:
```python
from core.db import Base, UUIDStringTimestampMixin

class Article(Base, UUIDStringTimestampMixin):
    __tablename__ = "articles"

    title: Mapped[str] = mapped_column(String(200))
    # Adds: id: str, created_at: datetime, updated_at: datetime
```

## Advanced Usage

### Raw SQL Queries
```python
from core.db import get_database_manager

db_manager = await get_database_manager()
result = await db_manager.execute_raw_sql(
    "SELECT * FROM users WHERE age > :age",
    {"age": 18}
)
```

### Health Monitoring
```python
from core.db import check_database_health

health_status = await check_database_health()
print(health_status)
# Output: {"status": "healthy", "connected": True, "database_url": "..."}
```

### Connection Context Manager
```python
from core.db import get_database_manager

db_manager = await get_database_manager()
async with db_manager.get_connection() as conn:
    result = await conn.execute("SELECT version()")
    version = result.scalar()
```

## Error Handling

The database system includes comprehensive error handling:

- **Connection Errors**: Automatic retry logic and graceful degradation
- **Transaction Errors**: Automatic rollback on exceptions
- **Health Check Failures**: Detailed error reporting
- **Session Management**: Proper cleanup and resource management

## Logging

All database operations are logged with appropriate levels:

```python
import logging

# Configure logging to see database operations
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("core.db")
```

## Configuration Options

### Engine Configuration
- **Connection Pooling**: Configurable pool size and behavior
- **Echo Mode**: SQL query logging for debugging
- **Connection Recycling**: Automatic connection refresh
- **Health Checks**: Pre-ping connections before use

### Session Configuration
- **Auto-commit**: Disabled by default for explicit transaction control
- **Auto-flush**: Enabled for immediate query execution
- **Expire on Commit**: Disabled to allow access to committed objects

## Best Practices

1. **Always use context managers** for sessions and connections
2. **Handle exceptions** appropriately in your application code
3. **Use the dependency injection** pattern with FastAPI
4. **Monitor database health** in production environments
5. **Configure logging** for debugging and monitoring
6. **Use environment variables** for configuration
7. **Implement proper error handling** for database operations

## Troubleshooting

### Common Issues

1. **Connection Refused**: Check PostgreSQL server is running and accessible
2. **Authentication Failed**: Verify credentials in environment variables
3. **Database Not Found**: Ensure the database exists
4. **Port Issues**: Check if the port is correct and not blocked

### Debug Mode

Enable debug mode for detailed logging:

```env
DEBUG=true
```

This will enable SQL query echoing and detailed connection logging.
