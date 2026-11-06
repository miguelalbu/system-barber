"""
Declarative base and the column helpers every model shares.

Two layers of tables:

* **Control plane** (`tenants`, `platform_admins`) — no `tenant_id`, no RLS.
  The registry of which shops exist and who, on our side, provides support.
* **Tenant data** (everything else) — every table inherits `TenantMixin` and
  gets an RLS policy in the migration that creates it (DEC-001).
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def pg_enum(source: type[enum.Enum], name: str) -> Enum:
    """
    A Postgres enum column.

    `values_callable` is mandatory: without it SQLAlchemy stores the member
    **name** ("TRIAL") while the database type expects the **value** ("trial").
    """
    return Enum(source, name=name, values_callable=lambda t: [m.value for m in t])


def uuid_pk() -> Mapped[uuid.UUID]:
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
