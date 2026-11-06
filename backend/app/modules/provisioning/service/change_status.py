from __future__ import annotations

import uuid

from app.core.database import control_session
from app.core.exceptions import Conflict
from app.modules.identity.public import TenantStatus
from app.modules.provisioning.dependencies import CoreCaller
from app.modules.provisioning.repository import audit as audit_repo
from app.modules.provisioning.schemas import CoreTenantOut
from app.modules.provisioning.service._lookup import tenant_or_404

# target → statuses it may come from. Repeating a transition is a no-op, so a
# retried call from the Core does not fail.
ALLOWED_FROM = {
    TenantStatus.SUSPENDED: {TenantStatus.ACTIVE, TenantStatus.SUSPENDED},
    TenantStatus.ACTIVE: {TenantStatus.SUSPENDED, TenantStatus.ACTIVE},
}


async def change_status(
    caller: CoreCaller, tenant_id: uuid.UUID, target: TenantStatus
) -> CoreTenantOut:
    """
    Suspend or resume: instant, reversible, no data touched. A suspended shop
    refuses logins and every request on its domain (403) until resumed.
    """
    async with control_session() as session:
        tenant = await tenant_or_404(session, tenant_id)
        if tenant.status not in ALLOWED_FROM[target]:
            raise Conflict(f"Não é possível passar de '{tenant.status}' para '{target}'")
        tenant.status = target
        audit_repo.record(
            session,
            core_key_id=caller.key_id,
            action=caller.action,
            target=tenant.slug,
            result=str(target),
            ip=caller.ip,
        )
        await session.flush()
        return CoreTenantOut.model_validate(tenant)
