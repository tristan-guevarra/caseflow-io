# matter and assignment db models

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Matter(Base):
    __tablename__ = "matters"
    __table_args__ = (Index("ix_matters_org_status", "organization_id", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    case_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    client_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    matter_type: Mapped[str] = mapped_column(
        Enum("litigation", "corporate", "real_estate", "ip", "employment", "family", "criminal", "other", name="matter_type_enum"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum("active", "pending", "closed", "archived", name="matter_status_enum"),
        default="active",
    )
    jurisdiction: Mapped[str | None] = mapped_column(String(255), nullable=True)
    opposing_party: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    opened_at: Mapped[date] = mapped_column(Date, default=date.today)
    closed_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    organization: Mapped["Organization"] = relationship(back_populates="matters")  # type: ignore[name-defined]  # noqa: F821
    assignments: Mapped[list["MatterAssignment"]] = relationship(back_populates="matter", cascade="all, delete-orphan")
    documents: Mapped[list["Document"]] = relationship(back_populates="matter", cascade="all, delete-orphan")  # type: ignore[name-defined]  # noqa: F821
    tasks: Mapped[list["Task"]] = relationship(back_populates="matter", cascade="all, delete-orphan")  # type: ignore[name-defined]  # noqa: F821
    timeline_events: Mapped[list["TimelineEvent"]] = relationship(back_populates="matter", cascade="all, delete-orphan")  # type: ignore[name-defined]  # noqa: F821


# tracks who is assigned to a matter and their role on it
class MatterAssignment(Base):
    __tablename__ = "matter_assignments"
    __table_args__ = (UniqueConstraint("matter_id", "user_id", name="uq_matter_assignment"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    matter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("matters.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(
        Enum("lead", "contributor", "viewer", name="assignment_role_enum"),
        default="contributor",
    )
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    matter: Mapped["Matter"] = relationship(back_populates="assignments")
    user: Mapped["User"] = relationship()  # type: ignore[name-defined]  # noqa: F821
