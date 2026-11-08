import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    SmallInteger,
    String,
    false,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.model_base import TenantBase

# Defaults confirmed by the owner (spec S01, Q-S01-5); the migration and the
# model share them so a fresh shop and a migrated one start the same.
DEFAULTS = {
    "min_advance_minutes": 60,
    "max_advance_days": 30,
    "confirmation_deadline_hours": 3,
    "client_change_min_hours": 2,
    "late_tolerance_minutes": 10,
    "max_future_appointments_per_client": 3,
}


def _int(name: str) -> Mapped[int]:
    return mapped_column(
        SmallInteger,
        nullable=False,
        default=DEFAULTS[name],
        server_default=text(str(DEFAULTS[name])),
    )


class ShopSettings(TenantBase):
    """
    Public contact and booking policies of the whole shop — a single row
    (`id = 1`). Policies are per shop, not per unit (Q-S01-4).
    """

    __tablename__ = "shop_settings"
    __table_args__ = (
        CheckConstraint("id = 1", name="ck_shop_settings_single_row"),
        CheckConstraint(
            "min_advance_minutes BETWEEN 0 AND 2880 AND min_advance_minutes % 15 = 0",
            name="ck_shop_settings_min_advance",
        ),
        CheckConstraint("max_advance_days BETWEEN 1 AND 180", name="ck_shop_settings_max_advance"),
        CheckConstraint(
            "confirmation_deadline_hours BETWEEN 1 AND 48", name="ck_shop_settings_confirmation"
        ),
        CheckConstraint(
            "client_change_min_hours BETWEEN 0 AND 72", name="ck_shop_settings_client_change"
        ),
        CheckConstraint("late_tolerance_minutes BETWEEN 0 AND 60", name="ck_shop_settings_late"),
        CheckConstraint(
            "max_future_appointments_per_client BETWEEN 1 AND 20",
            name="ck_shop_settings_future_limit",
        ),
    )

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, default=1)
    contact_phone: Mapped[str | None] = mapped_column(String(16))
    instagram: Mapped[str | None] = mapped_column(String(60))
    about: Mapped[str | None] = mapped_column(String(1000))
    min_advance_minutes: Mapped[int] = _int("min_advance_minutes")
    max_advance_days: Mapped[int] = _int("max_advance_days")
    confirmation_deadline_hours: Mapped[int] = _int("confirmation_deadline_hours")
    client_change_min_hours: Mapped[int] = _int("client_change_min_hours")
    late_tolerance_minutes: Mapped[int] = _int("late_tolerance_minutes")
    max_future_appointments_per_client: Mapped[int] = _int("max_future_appointments_per_client")
    # PD-41: the barber sees name and history, but phone and e-mail masked.
    barber_sees_client_contact: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    updated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
