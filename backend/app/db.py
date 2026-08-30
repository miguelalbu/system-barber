"""
Database access and tenant context.

This module is the **only** place in the system that opens a database session.
That is deliberate: the day a shop needs its own database, the change happens
here and nowhere else (see README, "Isolation").
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=False,
)

SessionFactory = async_sessionmaker(engine, expire_on_commit=False)

# Session variable read by the RLS policies.
TENANT_SETTING = "app.tenant_id"


async def set_tenant(session: AsyncSession, tenant_id: UUID | None) -> None:
    """
    Pin the tenant for the current transaction so RLS can filter on it.

    `set_config(key, value, is_local=True)` is the parameterizable equivalent of
    `SET LOCAL` — and the trailing `True` is what matters: the value dies with
    the transaction. With a plain `SET`, the tenant would stick to the pooled
    connection and the next request, from another shop, would inherit it.

    An empty string means "no tenant": the policies use
    `NULLIF(current_setting(...), '')::uuid`, so the comparison becomes NULL and
    no row is returned. Seeing nothing is the safe default.
    """
    await session.execute(
        text(f"SELECT set_config('{TENANT_SETTING}', :tid, true)"),
        {"tid": str(tenant_id) if tenant_id else ""},
    )


@asynccontextmanager
async def tenant_session(tenant_id: UUID | None) -> AsyncIterator[AsyncSession]:
    """Session with an open transaction and the tenant pinned. Commits on exit."""
    async with SessionFactory() as session:
        async with session.begin():
            await set_tenant(session, tenant_id)
            yield session


@asynccontextmanager
async def platform_session() -> AsyncIterator[AsyncSession]:
    """
    Tenant-less session for the control plane tables (`tenants`,
    `platform_admins`), which have no RLS. Use sparingly — any business query
    made here would bypass isolation.
    """
    async with SessionFactory() as session:
        async with session.begin():
            await set_tenant(session, None)
            yield session
