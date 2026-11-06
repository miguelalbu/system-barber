from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model_base import TenantBase, TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from app.modules.identity.model.user import User


class Barber(TenantBase, TimestampMixin):
    """
    The professional as a **scheduling resource**: a column on the calendar, a
    commission, a set of services.

    `user_id` is optional on purpose. Some barbers will never open the app — the
    front desk books for them — and they still need a calendar column.

    Lives in `identity` because it is born when an invite is accepted; revisit
    when the scheduling module exists (DEC-007).
    """

    __tablename__ = "barbers"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_barber_user"),
        Index("ix_barber_unit", "unit_id"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    unit_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("units.id", ondelete="RESTRICT"), nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    initials: Mapped[str] = mapped_column(String(4), nullable=False)
    default_commission: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=40)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user: Mapped[User | None] = relationship(back_populates="barber")
