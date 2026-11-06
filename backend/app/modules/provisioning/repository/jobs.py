import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.provisioning.model import ProvisioningJob


async def get(session: AsyncSession, job_id: uuid.UUID) -> ProvisioningJob | None:
    return await session.get(ProvisioningJob, job_id)


async def find_by_idempotency_key(session: AsyncSession, key: str) -> ProvisioningJob | None:
    return (
        await session.execute(select(ProvisioningJob).where(ProvisioningJob.idempotency_key == key))
    ).scalar_one_or_none()


async def latest_for_tenant(session: AsyncSession, tenant_id: uuid.UUID) -> ProvisioningJob | None:
    return (
        await session.execute(
            select(ProvisioningJob)
            .where(ProvisioningJob.tenant_id == tenant_id)
            .order_by(ProvisioningJob.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
