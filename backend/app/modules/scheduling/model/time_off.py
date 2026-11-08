import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.model_base import TenantBase, TimestampMixin, pg_enum, uuid_pk
from app.modules.scheduling.model.enums import TimeOffKind


class BarberTimeOff(TenantBase, TimestampMixin):
    """
    A period the barber does not work. Whole days are stored from local
    midnight of the first day to local midnight after the last one (T3);
    a `block` is a range inside one local day.
    """

    __tablename__ = "barber_time_off"
    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="ck_time_off_range"),
        ExcludeConstraint(
            ("barber_id", "="),
            (func.tstzrange("starts_at", "ends_at", "[)"), "&&"),
            name="ex_time_off_overlap",
            using="gist",
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    barber_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("barbers.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[TimeOffKind] = mapped_column(pg_enum(TimeOffKind, "time_off_kind"), nullable=False)
    all_day: Mapped[bool] = mapped_column(Boolean, nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(200))
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
