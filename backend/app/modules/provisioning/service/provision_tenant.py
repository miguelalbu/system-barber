from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError

from app.core.database import control_session
from app.core.exceptions import Conflict
from app.modules.identity.public import Tenant, TenantStatus, schema_name_for
from app.modules.provisioning.dependencies import CoreCaller
from app.modules.provisioning.model import ProvisioningJob
from app.modules.provisioning.repository import audit as audit_repo
from app.modules.provisioning.repository import catalog as catalog_repo
from app.modules.provisioning.repository import jobs as job_repo
from app.modules.provisioning.schemas import ProvisionAccepted, ProvisionIn


@dataclass
class ProvisionResult:
    accepted: ProvisionAccepted
    created: bool  # False = an earlier request for the same shop; nothing new was made


async def provision_tenant(
    caller: CoreCaller, data: ProvisionIn, idempotency_key: str | None
) -> ProvisionResult:
    """
    Validate, record and hand back the job (doc §6, "por que assíncrono"); the
    caller schedules `run_provisioning_job` after the commit.

    Idempotent twice over: a repeated `Idempotency-Key`, or the same slug, gets
    the job that already exists — never a second schema for one customer.
    """
    payload = data.model_dump(mode="json")
    async with control_session() as session:
        existing_job = (
            await job_repo.find_by_idempotency_key(session, idempotency_key)
            if idempotency_key
            else None
        )
        existing_tenant = (
            await catalog_repo.get(session, existing_job.tenant_id)
            if existing_job
            else await catalog_repo.find_by_slug(session, data.slug)
        )
        if existing_tenant is not None:
            job = existing_job or await job_repo.latest_for_tenant(session, existing_tenant.id)
            audit_repo.record(
                session,
                core_key_id=caller.key_id,
                action=caller.action,
                target=existing_tenant.slug,
                payload=payload,
                result="existing",
                ip=caller.ip,
            )
            return ProvisionResult(
                ProvisionAccepted(
                    tenant_id=existing_tenant.id, status=existing_tenant.status, job_id=job.id
                ),
                created=False,
            )

    async with control_session() as session:
        tenant = Tenant(
            slug=data.slug,
            schema_name=schema_name_for(data.slug),
            name=data.name,
            custom_domain=data.custom_domain,
            plan=data.plan,
            status=TenantStatus.PROVISIONING,
            external_tenant_id=data.external_tenant_id,
        )
        session.add(tenant)
        try:
            await session.flush()
        except IntegrityError as exc:
            # A race with a concurrent request for the same slug, or a domain or
            # Core id already taken by another shop.
            raise Conflict("Slug, domínio ou id externo já usado por outra barbearia") from exc

        job = ProvisioningJob(
            tenant_id=tenant.id,
            idempotency_key=idempotency_key,
            request={
                "owner_name": data.owner.name,
                "owner_email": data.owner.email,
                "unit_name": data.unit_name,
            },
        )
        session.add(job)
        await session.flush()
        audit_repo.record(
            session,
            core_key_id=caller.key_id,
            action=caller.action,
            target=tenant.slug,
            payload=payload,
            result="accepted",
            ip=caller.ip,
        )
        return ProvisionResult(
            ProvisionAccepted(tenant_id=tenant.id, status=tenant.status, job_id=job.id),
            created=True,
        )
