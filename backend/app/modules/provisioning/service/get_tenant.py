from __future__ import annotations

import uuid

from app.core.database import control_session
from app.modules.provisioning.dependencies import CoreCaller
from app.modules.provisioning.repository import audit as audit_repo
from app.modules.provisioning.repository import jobs as job_repo
from app.modules.provisioning.schemas import CoreTenantDetail, JobOut
from app.modules.provisioning.service._lookup import tenant_or_404


async def get_tenant(caller: CoreCaller, tenant_id: uuid.UUID) -> CoreTenantDetail:
    """
    The shop, its latest job and — **once** — the owner's first-access link.
    The link is erased as it is read: a secret that stays readable ends up in
    someone's terminal history.
    """
    async with control_session() as session:
        tenant = await tenant_or_404(session, tenant_id)
        job = await job_repo.latest_for_tenant(session, tenant.id)
        link = None
        if job is not None and job.setup_token_once:
            link, job.setup_token_once = job.setup_token_once, None
        audit_repo.record(
            session,
            core_key_id=caller.key_id,
            action=caller.action,
            target=tenant.slug,
            result="invite_delivered" if link else "ok",
            ip=caller.ip,
        )
        return CoreTenantDetail.model_validate(tenant).model_copy(
            update={"job": JobOut.model_validate(job) if job else None, "invite_link": link}
        )
