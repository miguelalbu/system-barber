from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model_base import TenantBase, TimestampMixin, pg_enum, uuid_pk
from app.modules.identity.model.enums import Role

if TYPE_CHECKING:
    from app.modules.identity.model.barber import Barber


class User(TenantBase, TimestampMixin):
    """
    A staff login: owner, manager, receptionist or barber.

    Email is unique **per shop** — each shop has its own `users` table in its own
    schema, and the shop comes from the access domain, so there is no ambiguity
    at login. End customers do not live here: they go to
    `clients`, with their own phone-based authentication.
    """

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_user_email"),
        Index("ix_user_active", "active"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[Role] = mapped_column(pg_enum(Role, "role"), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    units: Mapped[list[UserUnit]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    barber: Mapped[Barber | None] = relationship(back_populates="user", uselist=False)


class UserUnit(TenantBase):
    """
    Units the user can see. **An empty list means all of them** — the case for
    the owner and for single-unit shops, which are most of them.
    """

    __tablename__ = "user_units"
    __table_args__ = (UniqueConstraint("user_id", "unit_id", name="uq_user_unit"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    unit_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("units.id", ondelete="CASCADE"), nullable=False
    )

    user: Mapped[User] = relationship(back_populates="units")
