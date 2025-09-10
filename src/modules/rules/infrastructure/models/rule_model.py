"""Rule persistence model."""

import json
from uuid import UUID

from sqlalchemy import JSON, Enum as SQLEnum, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from core.db import Base, UUIDTimestampMixin
from modules.rules.domain.value_objects.enums import BalanceType, ProfileType, Status


class StringListType(TypeDecorator):
    """Custom type to handle string arrays for cross-database compatibility."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value):
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value):
        if value is not None:
            return json.loads(value)
        return value


class RuleModel(Base, UUIDTimestampMixin):
    """Rule persistence model for database storage."""

    __tablename__ = "rules"
    __table_args__ = {"extend_existing": True}

    # Basic fields
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    profile_type: Mapped[ProfileType] = mapped_column(SQLEnum(ProfileType), nullable=False)
    balance_type: Mapped[BalanceType] = mapped_column(SQLEnum(BalanceType), nullable=False)
    status: Mapped[Status] = mapped_column(SQLEnum(Status), nullable=False, default=Status.DRAFT)

    # Relationships
    section_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    # Configuration and metadata
    database_table_name: Mapped[list[str]] = mapped_column(StringListType, nullable=False)
    config: Mapped[dict] = mapped_column(JSON, nullable=False)

    def __repr__(self) -> str:
        return f"<RuleModel(id={self.id}, name='{self.name}', status={self.status})>"
