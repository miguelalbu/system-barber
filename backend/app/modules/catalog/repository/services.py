import uuid
from collections.abc import Iterable

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.model import Service


async def list_all(
    session: AsyncSession, *, active: bool | None = None, ids: Iterable[uuid.UUID] | None = None
) -> list[Service]:
    stmt = select(Service)
    if active is not None:
        stmt = stmt.where(Service.active.is_(active))
    if ids is not None:
        stmt = stmt.where(Service.id.in_(list(ids)))
    return list((await session.execute(stmt.order_by(func.lower(Service.name)))).scalars())


async def get(session: AsyncSession, service_id: uuid.UUID) -> Service | None:
    """Fresh from the database (also reloads what a flush expired, like `updated_at`)."""
    stmt = select(Service).where(Service.id == service_id).execution_options(populate_existing=True)
    return (await session.execute(stmt)).scalar_one_or_none()


async def name_taken(
    session: AsyncSession, name: str, *, exclude_id: uuid.UUID | None = None
) -> bool:
    stmt = select(Service.id).where(func.lower(Service.name) == name.lower())
    if exclude_id is not None:
        stmt = stmt.where(Service.id != exclude_id)
    return (await session.execute(stmt.limit(1))).first() is not None


async def existing_ids(session: AsyncSession, ids: Iterable[uuid.UUID]) -> set[uuid.UUID]:
    return set(
        (await session.execute(select(Service.id).where(Service.id.in_(list(ids))))).scalars()
    )
