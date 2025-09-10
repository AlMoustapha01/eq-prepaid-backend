"""Section persistence model."""

from sqlalchemy import Enum as SQLEnum, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base, UUIDTimestampMixin
from modules.rules.domain.models.section import SectionStatus


class SectionModel(Base, UUIDTimestampMixin):
    """Section persistence model for database storage."""

    __tablename__ = "sections"
    __table_args__ = (
        Index("ix_sections_slug", "slug", unique=True),
        Index("ix_sections_status", "status"),
        Index(
            "ix_sections_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
        {"extend_existing": True},
    )

    name: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True, doc="Name of the section"
    )

    slug: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        doc="URL-friendly slug for the section",
    )

    description: Mapped[str] = mapped_column(
        Text, nullable=True, doc="Detailed description of the section"
    )

    status: Mapped[SectionStatus] = mapped_column(
        SQLEnum(SectionStatus, name="section_status_enum", create_constraint=True),
        nullable=False,
        default=SectionStatus.ACTIVE,
        server_default=SectionStatus.ACTIVE.value,
        doc="Current status of the section",
    )

    rules: Mapped[list["RuleModel"]] = relationship(
        "RuleModel",
        back_populates="section",
        cascade="all, delete-orphan",
        doc="Rules belonging to this section",
    )
