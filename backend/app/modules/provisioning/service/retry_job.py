from __future__ import annotations

import uuid

from app.core.database import control_session
from app.core.exceptions import Conflict
from app.modules.identity.public import TenantStatus
from app.modules.provisioning.dependencies import CoreCaller
from app.modules.provisioning.model import JobStatus
from app.modules.provisioning.repository import audit as audit_repo
from app.modules.provisioning.repository import jobs as job_repo
from app.modules.provisioning.schemas import ProvisionAccepted
from app.modules.provisioning.service._lookup import tenant_or_404


async def retry_job(caller: CoreCaller, tenant_id: uuid.UUID) -> ProvisionAccepted:
    """
    Resume a job that did not finish. Safe because every step is idempotent;
    the caller schedules `run_provisioning_job` again.
    """
    async with control_session() as session:
        tenant = await tenant_or_404(session, tenant_id)
        job = await job_repo.latest_for_tenant(session, tenant.id)
        if job is None or job.status is JobStatus.SUCCEEDED:
            raise Conflict("A barbearia já está provisionada")
        job.status = JobStatus.PENDING
        tenant.status = TenantStatus.PROVISIONING
        audit_repo.record(
            session,
            core_key_id=caller.key_id,
            action=caller.action,
            target=tenant.slug,
            result=f"retry_from:{job.step}",
            ip=caller.ip,
        )
        return ProvisionAccepted(tenant_id=tenant.id, status=tenant.status, job_id=job.id)
