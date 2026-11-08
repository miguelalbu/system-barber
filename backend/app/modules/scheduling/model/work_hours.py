import uuid
from datetime import time

from sqlalchemy import CheckConstraint, ForeignKey, Index, SmallInteger, Time
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.model_base import TenantBase, uuid_pk


class BarberWorkHours(TenantBase):
    """
    One working interval of a barber on a weekday (ISO 1–7). Lunch is the gap
    between two intervals (T1). A barber with no row follows the unit's hours (T2).
    """

    __tablename__ = "barber_work_hours"
    __table_args__ = (
        CheckConstraint("weekday BETWEEN 1 AND 7", name="ck_barber_hours_weekday"),
        CheckConstraint("starts_at < ends_at", name="ck_barber_hours_interval"),
        Index("ix_barber_hours_barber_weekday", "barber_id", "weekday"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    barber_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("barbers.id", ondelete="CASCADE"), nullable=False
    )
    weekday: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    starts_at: Mapped[time] = mapped_column(Time, nullable=False)
    ends_at: Mapped[time] = mapped_column(Time, nullable=False)
