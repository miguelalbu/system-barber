import uuid

from sqlalchemy import Boolean, Index, String, Text, text, true
from sqlalchemy.orm import Mapped, mapped_column

from app.core.model_base import TenantBase, TimestampMixin, uuid_pk


class Unit(TenantBase, TimestampMixin):
    """A shop location. One tenant has one or many; the plan caps how many are active."""

    __tablename__ = "units"
    __table_args__ = (
        # Case-insensitive: "Centro" and "centro" are the same unit.
        Index("uq_unit_name", text("lower(name)"), unique=True),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="America/Sao_Paulo")
    # Text in the database; the 300-character cap is a schema rule (spec S01, Notes).
    address: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(String(32))
    # Offered to the AI and the public booking link.
    online_booking: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
