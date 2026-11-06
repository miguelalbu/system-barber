from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model_base import Base, TimestampMixin, pg_enum, uuid_pk
from app.modules.identity.model.enums import TenantStatus

if TYPE_CHECKING:
    from app.modules.identity.model.unit import Unit


class Tenant(Base, TimestampMixin):
    """A barbershop — its own business, tax id and subscription. Control plane, no RLS."""

    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = uuid_pk()
    slug: Mapped[str] = mapped_column(String(63), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    # Own domain pointed here by CNAME. When null, the shop is served at
    # <slug>.<base_domain>.
    custom_domain: Mapped[str | None] = mapped_column(String(255), unique=True)

    plan: Mapped[str] = mapped_column(String(40), nullable=False, default="basic")
    status: Mapped[TenantStatus] = mapped_column(
        pg_enum(TenantStatus, "tenant_status"), nullable=False, default=TenantStatus.TRIAL
    )

    units: Mapped[list[Unit]] = relationship(back_populates="tenant")
