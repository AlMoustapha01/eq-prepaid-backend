"""Rule persistence model."""

from uuid import UUID

from sqlalchemy import ARRAY, JSON, Enum as SQLEnum, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base, UUIDTimestampMixin
from modules.rules.domain.value_objects.enums import BalanceType, ProfileType, RuleStatus
from modules.rules.infrastructure.models.section_model import SectionModel


class RuleModel(Base, UUIDTimestampMixin):
    """Rule persistence model for database storage."""

    __tablename__ = "rules"
    __table_args__ = (
        Index("ix_rules_section_id_status", "section_id", "status"),
        Index("ix_rules_profile_balance", "profile_type", "balance_type"),
        Index(
            "ix_rules_name", "name", postgresql_using="gin", postgresql_ops={"name": "gin_trgm_ops"}
        ),
        Index("ux_rules_section_name", "section_id", "name", unique=True),
        {"extend_existing": True},
    )

    name: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True, doc="Unique name of the rule within its section"
    )

    profile_type: Mapped[ProfileType] = mapped_column(
        SQLEnum(ProfileType, name="profile_type_enum"),
        nullable=False,
        doc="Type of profile this rule applies to",
    )

    balance_type: Mapped[BalanceType] = mapped_column(
        SQLEnum(BalanceType, name="balance_type_enum"),
        nullable=False,
        doc="Type of balance this rule affects",
    )

    status: Mapped[RuleStatus] = mapped_column(
        SQLEnum(RuleStatus, name="rule_status_enum"),
        nullable=False,
        default=RuleStatus.DRAFT,
        server_default=RuleStatus.DRAFT.value,
        doc="Current status of the rule",
    )

    section_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sections.id", ondelete="CASCADE"),
        nullable=False,
        doc="Foreign key to the sections table",
    )

    section: Mapped[SectionModel] = relationship("SectionModel", back_populates="rules")

    database_table_name: Mapped[list[str]] = mapped_column(
        ARRAY(String(255)),
        nullable=False,
        doc="List of database tables this rule applies to",
        server_default="{}",
    )

    config: Mapped[dict] = mapped_column(
        JSON(none_as_null=True),
        nullable=False,
        doc="Rule configuration parameters in JSON format",
        server_default="{}",
    )
