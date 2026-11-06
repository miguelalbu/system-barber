import uuid

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.model_base import Base, TimestampMixin, uuid_pk


class PlatformAdmin(Base, TimestampMixin):
    """Our own staff, for cross-tenant support. Outside the tenant RBAC, no RLS (DEC-003)."""

    __tablename__ = "platform_admins"

    id: Mapped[uuid.UUID] = uuid_pk()
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
