from __future__ import annotations

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import Conflict
from app.modules.identity.model import Tenant
from app.modules.identity.repository import tenants as tenant_repo
from app.modules.identity.schemas import TenantUpdate


async def update_tenant(session: AsyncSession, tenant_id: uuid.UUID, data: TenantUpdate) -> Tenant:
    """
    Rename the shop or point a custom domain at it.

    `tenants` is control plane and has no RLS, so this runs on a platform
    session carrying no tenant — which is why the lookup is by explicit id.
    """
    tenant = await tenant_repo.get_by_id(session, tenant_id)

    if data.name is not None:
        tenant.name = data.name
    if data.custom_domain is not None:
        tenant.custom_domain = data.custom_domain.lower().strip() or None

    try:
        await session.flush()
    except IntegrityError as exc:
        raise Conflict("Esse domínio já está em uso por outra barbearia") from exc

    return tenant
