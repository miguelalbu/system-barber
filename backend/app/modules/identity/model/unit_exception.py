import uuid
from datetime import date, time

from sqlalchemy import CheckConstraint, Date, ForeignKey, String, Time, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.model_base import TenantBase, TimestampMixin, pg_enum, uuid_pk
from app.modules.identity.model.enums import UnitExceptionKind


class UnitException(TenantBase, TimestampMixin):
    """
    A date range where a unit's weekly hours do not apply: closed (holiday,
    renovation) or open on one special interval (Christmas Eve 08:00–14:00).
    It wins over the weekly hours on its days.
    """

    __tablename__ = "unit_exceptions"
    __table_args__ = (
        CheckConstraint("ends_on >= starts_on", name="ck_unit_exception_dates"),
        CheckConstraint(
            "(kind = 'closed' AND opens_at IS NULL AND closes_at IS NULL)"
            " OR (kind = 'special_hours' AND opens_at < closes_at)",
            name="ck_unit_exception_hours",
        ),
        # Two exceptions of one unit never overlap (needs btree_gist, control c0002).
        ExcludeConstraint(
            ("unit_id", "="),
            (func.daterange("starts_on", "ends_on", "[]"), "&&"),
            name="ex_unit_exception_overlap",
            using="gist",
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    unit_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("units.id", ondelete="CASCADE"), nullable=False
    )
    starts_on: Mapped[date] = mapped_column(Date, nullable=False)
    ends_on: Mapped[date] = mapped_column(Date, nullable=False)
    kind: Mapped[UnitExceptionKind] = mapped_column(
        pg_enum(UnitExceptionKind, "unit_exception_kind"), nullable=False
    )
    opens_at: Mapped[time | None] = mapped_column(Time)
    closes_at: Mapped[time | None] = mapped_column(Time)
    reason: Mapped[str | None] = mapped_column(String(120))
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
