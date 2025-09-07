"""Section persistence model."""

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base, UUIDTimestampMixin
from modules.rules.domain.models.section import SectionStatus


class SectionModel(Base, UUIDTimestampMixin):
    """Section persistence model for database storage."""

    __tablename__ = "sections"
    __table_args__ = {"extend_existing": True}

    # Basic fields
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[SectionStatus] = mapped_column(
        SQLEnum(SectionStatus), nullable=False, default=SectionStatus.ACTIVE
    )

    def __repr__(self) -> str:
        return f"<SectionModel(id={self.id}, name='{self.name}', slug='{self.slug}', status={self.status})>"
