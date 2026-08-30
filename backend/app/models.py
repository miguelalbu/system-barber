"""
Identity and tenancy core.

Two layers:

* **Control plane** (`tenants`, `platform_admins`) — no `tenant_id`, no RLS.
  The registry of which shops exist and who, on our side, provides support.
* **Tenant data** (everything else) — every table carries `tenant_id` and has an
  RLS policy. See migration 0001 for the policies.

Domain modules (scheduling, finance, CRM) arrive as their own files later; they
inherit `TenantMixin` and get their policy in their own migration.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _enum(source: type[enum.Enum], name: str) -> Enum:
    """
    A Postgres enum column.

    `values_callable` is mandatory: without it SQLAlchemy stores the member
    **name** ("TRIAL") while the database type expects the **value** ("trial").
    """
    return Enum(source, name=name, values_callable=lambda t: [m.value for m in t])


def _pk() -> Mapped[uuid.UUID]:
    return mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class TenantMixin:
    """
    Every table holding shop data inherits this.

    The column stays even if some shop eventually gets its own database — it is
    precisely what makes that migration possible without reshaping the schema.
    """

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )


# --------------------------------------------------------------------------- #
# Control plane
# --------------------------------------------------------------------------- #


class TenantStatus(enum.StrEnum):
    TRIAL = "trial"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELED = "canceled"


class Tenant(Base, TimestampMixin):
    """A barbershop — its own business, tax id and subscription."""

    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = _pk()
    slug: Mapped[str] = mapped_column(String(63), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    # Own domain pointed here by CNAME. When null, the shop is served at
    # <slug>.<base_domain>.
    custom_domain: Mapped[str | None] = mapped_column(String(255), unique=True)

    plan: Mapped[str] = mapped_column(String(40), nullable=False, default="basic")
    status: Mapped[TenantStatus] = mapped_column(
        _enum(TenantStatus, "tenant_status"), nullable=False, default=TenantStatus.TRIAL
    )

    units: Mapped[list[Unit]] = relationship(back_populates="tenant")


class PlatformAdmin(Base, TimestampMixin):
    """Our own staff, for cross-tenant support. Outside the tenant RBAC."""

    __tablename__ = "platform_admins"

    id: Mapped[uuid.UUID] = _pk()
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


# --------------------------------------------------------------------------- #
# Tenant data
# --------------------------------------------------------------------------- #


class Role(enum.StrEnum):
    OWNER = "owner"
    MANAGER = "manager"
    RECEPTIONIST = "receptionist"
    BARBER = "barber"


class Unit(Base, TenantMixin, TimestampMixin):
    """A shop location. One tenant has one or many; the Multi plan bills per unit."""

    __tablename__ = "units"

    id: Mapped[uuid.UUID] = _pk()
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="America/Sao_Paulo")
    address: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(String(32))
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    tenant: Mapped[Tenant] = relationship(back_populates="units")


class User(Base, TenantMixin, TimestampMixin):
    """
    A staff login: owner, manager, receptionist or barber.

    Email is unique **per shop** — the tenant comes from the access domain, so
    there is no ambiguity at login. End customers do not live here: they go to
    `clients`, with their own phone-based authentication.
    """

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_user_tenant_email"),
        Index("ix_user_tenant_active", "tenant_id", "active"),
    )

    id: Mapped[uuid.UUID] = _pk()
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[Role] = mapped_column(_enum(Role, "role"), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    units: Mapped[list[UserUnit]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    barber: Mapped[Barber | None] = relationship(back_populates="user", uselist=False)


class UserUnit(Base, TenantMixin):
    """
    Units the user can see. **An empty list means all of them** — the case for
    the owner and for single-unit shops, which are most of them.
    """

    __tablename__ = "user_units"
    __table_args__ = (UniqueConstraint("user_id", "unit_id", name="uq_user_unit"),)

    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    unit_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("units.id", ondelete="CASCADE"), nullable=False
    )

    user: Mapped[User] = relationship(back_populates="units")


class Barber(Base, TenantMixin, TimestampMixin):
    """
    The professional as a **scheduling resource**: a column on the calendar, a
    commission, a set of services.

    `user_id` is optional on purpose. Some barbers will never open the app — the
    front desk books for them — and they still need a calendar column.
    """

    __tablename__ = "barbers"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_barber_user"),
        Index("ix_barber_tenant_unit", "tenant_id", "unit_id"),
    )

    id: Mapped[uuid.UUID] = _pk()
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


class RefreshToken(Base, TenantMixin):
    """
    Rotating refresh token. Only the hash is stored — a database leak does not
    let anyone forge a session. `revoked_at` gives immediate logout without
    waiting for the access token to expire.
    """

    __tablename__ = "refresh_tokens"
    __table_args__ = (Index("ix_refresh_user_active", "user_id", "revoked_at"),)

    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Invite(Base, TenantMixin):
    """A team invite. This is how a user is born without a seeded password."""

    __tablename__ = "invites"
    __table_args__ = (Index("ix_invite_tenant_email", "tenant_id", "email"),)

    id: Mapped[uuid.UUID] = _pk()
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[Role] = mapped_column(_enum(Role, "role"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Decisions made when inviting, applied when the invite is accepted.
    unit_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(PgUUID(as_uuid=True)), nullable=False, default=list
    )
    create_barber: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
