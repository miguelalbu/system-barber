from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFound
from app.modules.identity.public import Tenant
from app.modules.provisioning.repository import catalog as catalog_repo


async def tenant_or_404(session: AsyncSession, tenant_id: uuid.UUID) -> Tenant:
    tenant = await catalog_repo.get(session, tenant_id)
    if tenant is None:
        raise NotFound("Barbearia não encontrada")
    return tenant
