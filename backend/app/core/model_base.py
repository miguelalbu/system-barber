"""
Declarative bases and the column helpers every model shares.

Two bases, two schemas (DEC-011):

* **`ControlBase`** — the control plane, in `public`: which shops exist, the
  control-plane credentials, provisioning jobs, audit. Never shop data. No
  schema in the metadata — it resolves to `public`, the runtime role's
  search_path, and is never translated.
* **`TenantBase`** — a shop's own tables, under the placeholder schema
  `tenant`. A tenant session's `schema_translate_map` swaps the placeholder for
  the shop's `tenant_<slug>` in every table and enum. Used outside a tenant
  session, the SQL points at a schema named `tenant` that does not exist and
  **fails** — it can never fall through to `public`. There is no `tenant_id`
  column: the schema is the boundary.

A foreign key never crosses the two bases.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, MetaData, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

CONTROL_SCHEMA = "public"
# Never a real schema: always translated to the shop's schema at runtime.
TENANT_SCHEMA_PLACEHOLDER = "tenant"


class ControlBase(DeclarativeBase):
    metadata = MetaData()


class TenantBase(DeclarativeBase):
    metadata = MetaData(schema=TENANT_SCHEMA_PLACEHOLDER)


def pg_enum(source: type[enum.Enum], name: str) -> Enum:
    """
    A Postgres enum column.

    `values_callable` is mandatory: without it SQLAlchemy stores the member
    **name** ("ACTIVE") while the database type expects the **value** ("active").
    The type takes the schema of its metadata: `public` for the control plane,
    the placeholder `tenant` — so the shop's own schema at runtime — for shop
    tables. Each shop has its own copy of its enum types (doc §2), so no
    tenant role needs `public`.
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
