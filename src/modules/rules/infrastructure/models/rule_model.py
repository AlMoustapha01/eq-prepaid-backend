"""Rule persistence model."""

from uuid import UUID

from sqlalchemy import JSON
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base, UUIDTimestampMixin
from modules.rules.domain.value_objects.enums import BalanceType, ProfileType, Status


class RuleModel(Base, UUIDTimestampMixin):
    """Rule persistence model for database storage."""

    __tablename__ = "rules"

    # Basic fields
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    profile_type: Mapped[ProfileType] = mapped_column(SQLEnum(ProfileType), nullable=False)
    balance_type: Mapped[BalanceType] = mapped_column(SQLEnum(BalanceType), nullable=False)
    status: Mapped[Status] = mapped_column(SQLEnum(Status), nullable=False, default=Status.DRAFT)

    # Relationships
    section_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    # Configuration and metadata
    database_table_name: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    config: Mapped[dict] = mapped_column(JSON, nullable=False)

    def __repr__(self) -> str:
        return f"<RuleModel(id={self.id}, name='{self.name}', status={self.status})>"
