import uuid
from datetime import date, datetime, time

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, String, Time, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.model_base import TenantBase, uuid_pk


class BarberShiftOverride(TenantBase):
    """One interval of a special shift: on `on_date` these rows replace the weekly schedule."""

    __tablename__ = "barber_shift_overrides"
    __table_args__ = (
        CheckConstraint("starts_at < ends_at", name="ck_shift_override_interval"),
        Index("ix_shift_override_barber_date", "barber_id", "on_date"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    barber_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("barbers.id", ondelete="CASCADE"), nullable=False
    )
    on_date: Mapped[date] = mapped_column(Date, nullable=False)
    starts_at: Mapped[time] = mapped_column(Time, nullable=False)
    ends_at: Mapped[time] = mapped_column(Time, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(120))
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
