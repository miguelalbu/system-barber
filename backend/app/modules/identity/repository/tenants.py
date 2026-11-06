"""`tenants` is control plane: no RLS, so every query here filters explicitly."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.model import Tenant


async def get_by_id(session: AsyncSession, tenant_id: uuid.UUID) -> Tenant:
    return (await session.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one()


async def find_by_slug(session: AsyncSession, slug: str) -> Tenant | None:
    return (await session.execute(select(Tenant).where(Tenant.slug == slug))).scalar_one_or_none()


async def find_by_custom_domain(session: AsyncSession, host: str) -> Tenant | None:
    return (
        await session.execute(select(Tenant).where(Tenant.custom_domain == host))
    ).scalar_one_or_none()
