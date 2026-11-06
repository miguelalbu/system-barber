import uuid
from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.model import Unit


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


async def first_id(session: AsyncSession) -> uuid.UUID:
    """The oldest unit — the default home for a barber invited without one."""
    return (await session.execute(select(Unit.id).order_by(Unit.created_at).limit(1))).scalar_one()


async def any_exists(session: AsyncSession) -> bool:
    return (await session.execute(select(Unit.id).limit(1))).first() is not None
