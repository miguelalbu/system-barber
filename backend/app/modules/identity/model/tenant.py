import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.model_base import ControlBase, TimestampMixin, pg_enum, uuid_pk
from app.modules.identity.model.enums import TenantStatus


class Tenant(ControlBase, TimestampMixin):
    """
    A barbershop, as the control plane knows it. Its data lives in its own
    schema (`schema_name`); this row is the catalog entry that routes to it.

    The future Core owns the customer's identity — `external_tenant_id` is the
    Core's id for this shop, which correlates it across products (doc §6).
    """

    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = uuid_pk()
    # The subdomain: <slug>.<base_domain>. DNS-safe, so it may contain hyphens.
    slug: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    # Written once at provisioning and read from here forever — never derived
    # again from user input (doc §6, "slug é superfície de injeção de DDL").
    schema_name: Mapped[str] = mapped_column(String(63), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    # Own domain pointed here by CNAME. When null, the shop is served at
    # <slug>.<base_domain>.
    custom_domain: Mapped[str | None] = mapped_column(String(255), unique=True)

    plan: Mapped[str] = mapped_column(String(40), nullable=False, default="basic")
    status: Mapped[TenantStatus] = mapped_column(
        pg_enum(TenantStatus, "tenant_status"), nullable=False, default=TenantStatus.PROVISIONING
    )
    # Tenant migration revision the schema reports having; None until the first
    # migrate run records it. The API refuses a schema that is behind.
    schema_version: Mapped[str | None] = mapped_column(String(32))
    external_tenant_id: Mapped[str | None] = mapped_column(String(120), unique=True)
