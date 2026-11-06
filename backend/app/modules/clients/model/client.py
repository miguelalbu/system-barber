import uuid
from datetime import date

from sqlalchemy import Boolean, Date, String, UniqueConstraint, true
from sqlalchemy.orm import Mapped, mapped_column

from app.core.model_base import TenantBase, TimestampMixin, uuid_pk


class Client(TenantBase, TimestampMixin):
    """
    An end customer of the shop. Not a staff login (`users`): clients will
    authenticate by phone + OTP, in their own spec.
    """

    __tablename__ = "clients"
    __table_args__ = (UniqueConstraint("phone", name="uq_client_phone"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    # E.164 ("+5511987654321"), normalized by `app.modules.clients.phone`.
    phone: Mapped[str] = mapped_column(String(16), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    birth_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(String(1000))
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
