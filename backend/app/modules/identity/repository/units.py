import uuid
from collections.abc import Iterable

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.model import Barber, Unit, UserUnit


async def list_visible(
    session: AsyncSession,
    *,
    unit_ids: list[uuid.UUID] | None,
    active_only: bool = False,
) -> list[Unit]:
    """Units ordered by name. `unit_ids=None` means every unit of the shop."""
    stmt = select(Unit)
    if active_only:
        stmt = stmt.where(Unit.active.is_(True))
    if unit_ids is not None:
        stmt = stmt.where(Unit.id.in_(unit_ids))
    return list((await session.execute(stmt.order_by(Unit.name))).scalars())


async def existing_ids(session: AsyncSession, unit_ids: Iterable[uuid.UUID]) -> set[uuid.UUID]:
    return set((await session.execute(select(Unit.id).where(Unit.id.in_(unit_ids)))).scalars())


async def any_exists(session: AsyncSession) -> bool:
    return (await session.execute(select(Unit.id).limit(1))).first() is not None


async def get(session: AsyncSession, unit_id: uuid.UUID) -> Unit | None:
    return await session.get(Unit, unit_id, populate_existing=True)


async def name_taken(
    session: AsyncSession, name: str, *, exclude_id: uuid.UUID | None = None
) -> bool:
    stmt = select(Unit.id).where(func.lower(Unit.name) == name.lower())
    if exclude_id is not None:
        stmt = stmt.where(Unit.id != exclude_id)
    return (await session.execute(stmt.limit(1))).first() is not None


async def count_active(session: AsyncSession, *, exclude_id: uuid.UUID | None = None) -> int:
    stmt = select(func.count()).select_from(Unit).where(Unit.active.is_(True))
    if exclude_id is not None:
        stmt = stmt.where(Unit.id != exclude_id)
    return (await session.execute(stmt)).scalar_one()


async def has_active_barbers(session: AsyncSession, unit_id: uuid.UUID) -> bool:
    stmt = select(Barber.id).where(Barber.unit_id == unit_id, Barber.active.is_(True)).limit(1)
    return (await session.execute(stmt)).first() is not None


async def has_user_links(session: AsyncSession, unit_id: uuid.UUID) -> bool:
    stmt = select(UserUnit.user_id).where(UserUnit.unit_id == unit_id).limit(1)
    return (await session.execute(stmt)).first() is not None
