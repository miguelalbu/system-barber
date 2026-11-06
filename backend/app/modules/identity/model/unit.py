from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model_base import Base, TenantMixin, TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from app.modules.identity.model.tenant import Tenant


class Unit(Base, TenantMixin, TimestampMixin):
    """A shop location. One tenant has one or many; the Multi plan bills per unit."""

    __tablename__ = "units"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="America/Sao_Paulo")
    address: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(String(32))
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    tenant: Mapped[Tenant] = relationship(back_populates="units")
