from __future__ import annotations

import uuid

from sqlalchemy import text

from app.core.database import control_session, migrator_engine, quote_identifier
from app.core.exceptions import BadRequest, Conflict
from app.modules.identity.public import TenantStatus
from app.modules.provisioning.dependencies import CoreCaller
from app.modules.provisioning.repository import audit as audit_repo
from app.modules.provisioning.schemas import DestroyIn
from app.modules.provisioning.service._lookup import tenant_or_404


async def destroy_tenant(caller: CoreCaller, tenant_id: uuid.UUID, data: DestroyIn) -> None:
    """
    Delete a shop's data for good (LGPD erasure, cancellation). Four gates at
    once (doc §6): the `tenant:destroy` scope (checked by the route), the shop
    already suspended, its slug typed again, and the export confirmed.

    The schema and the shop's role are dropped; the catalog row stays as
    `archived` — the history that the customer existed has value — and the
    domain stops resolving (archived answers like unknown).
    """
    async with control_session() as session:
        tenant = await tenant_or_404(session, tenant_id)
        if tenant.status is not TenantStatus.SUSPENDED:
            raise Conflict("Suspenda a barbearia antes de excluí-la")
        if data.confirm != tenant.slug:
            raise BadRequest("A confirmação não confere com o slug da barbearia")
        if not data.exported:
            raise BadRequest("Exporte os dados (pg_dump do schema) antes de excluir")
        schema = tenant.schema_name

    q = quote_identifier(schema)
    async with migrator_engine().begin() as conn:
        await conn.execute(text(f"DROP SCHEMA IF EXISTS {q} CASCADE"))
        role_exists = await conn.scalar(
            text("SELECT 1 FROM pg_roles WHERE rolname = :name"), {"name": schema}
        )
        if role_exists:
            await conn.execute(text(f"DROP OWNED BY {q}"))
            await conn.execute(text(f"DROP ROLE {q}"))

    async with control_session() as session:
        tenant = await tenant_or_404(session, tenant_id)
        tenant.status = TenantStatus.ARCHIVED
        tenant.custom_domain = None
        audit_repo.record(
            session,
            core_key_id=caller.key_id,
            action=caller.action,
            target=tenant.slug,
            payload={"confirm": data.confirm, "exported": data.exported},
            result="destroyed",
            ip=caller.ip,
        )
