# Generate new migration

poetry run alembic revision --autogenerate -m "Description"

# Apply migrations

poetry run alembic upgrade head

# Rollback migrations

poetry run alembic downgrade -1

# Check current migration status

poetry run alembic current

# View migration history

poetry run alembic history

# Run tests

poetry run pytest

# Run server

poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run ruff

poetry run ruff check --fix .

# Run pre-commit

poetry run pre-commit run --all-files
