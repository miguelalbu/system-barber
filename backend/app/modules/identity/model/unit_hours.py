import uuid
from datetime import time

from sqlalchemy import CheckConstraint, ForeignKey, Index, SmallInteger, Time
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.model_base import TenantBase, uuid_pk


class UnitBusinessHours(TenantBase):
    """
    One opening interval of a unit on a weekday (ISO: 1 = Monday … 7 = Sunday).
    A day with no row is closed; up to three intervals a day (spec S01).
    Times are wall-clock in the unit's timezone and never cross midnight.
    """

    __tablename__ = "unit_business_hours"
    __table_args__ = (
        CheckConstraint("weekday BETWEEN 1 AND 7", name="ck_unit_hours_weekday"),
        CheckConstraint("opens_at < closes_at", name="ck_unit_hours_interval"),
        Index("ix_unit_hours_unit_weekday", "unit_id", "weekday"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    unit_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("units.id", ondelete="CASCADE"), nullable=False
    )
    weekday: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    opens_at: Mapped[time] = mapped_column(Time, nullable=False)
    closes_at: Mapped[time] = mapped_column(Time, nullable=False)
