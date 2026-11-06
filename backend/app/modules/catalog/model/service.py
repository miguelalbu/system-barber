import uuid

from sqlalchemy import Boolean, CheckConstraint, Index, Integer, SmallInteger, String, text, true
from sqlalchemy.orm import Mapped, mapped_column

from app.core.model_base import TenantBase, TimestampMixin, uuid_pk


class Service(TenantBase, TimestampMixin):
    """
    Something the shop sells and books: "Corte", "Barba", "Corte + Barba".

    One price for every unit (spec P4); a per-unit override can come later
    without changing this table. Money is integer cents (P6).
    """

    __tablename__ = "services"
    __table_args__ = (
        # Case-insensitive: "Corte" and "corte" are the same service.
        Index("uq_service_name", text("lower(name)"), unique=True),
        CheckConstraint(
            "duration_minutes BETWEEN 5 AND 480 AND duration_minutes % 5 = 0",
            name="ck_service_duration",
        ),
        CheckConstraint("price_cents >= 0", name="ck_service_price"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    duration_minutes: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
