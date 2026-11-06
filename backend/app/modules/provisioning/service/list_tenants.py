from __future__ import annotations

from app.core.database import control_session
from app.modules.provisioning.dependencies import CoreCaller
from app.modules.provisioning.repository import audit as audit_repo
from app.modules.provisioning.repository import catalog as catalog_repo
from app.modules.provisioning.schemas import CoreTenantOut


async def list_tenants(caller: CoreCaller) -> list[CoreTenantOut]:
    """Every shop, for the Core to reconcile against its own records."""
    async with control_session() as session:
        tenants = await catalog_repo.list_all(session)
        audit_repo.record(
            session, core_key_id=caller.key_id, action=caller.action, result="ok", ip=caller.ip
        )
        return [CoreTenantOut.model_validate(t) for t in tenants]
