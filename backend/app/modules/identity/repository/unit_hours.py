import uuid
from collections.abc import Iterable
from datetime import time

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.model import UnitBusinessHours


async def list_for(session: AsyncSession, unit_ids: Iterable[uuid.UUID]) -> list[UnitBusinessHours]:
    stmt = (
        select(UnitBusinessHours)
        .where(UnitBusinessHours.unit_id.in_(list(unit_ids)))
        .order_by(UnitBusinessHours.weekday, UnitBusinessHours.opens_at)
    )
    return list((await session.execute(stmt)).scalars())


async def replace(
    session: AsyncSession, unit_id: uuid.UUID, rows: Iterable[tuple[int, time, time]]
) -> None:
    """The whole week at once: what is not sent is closed."""
    await session.execute(delete(UnitBusinessHours).where(UnitBusinessHours.unit_id == unit_id))
    session.add_all(
        UnitBusinessHours(unit_id=unit_id, weekday=wd, opens_at=opens, closes_at=closes)
        for wd, opens, closes in rows
    )
    await session.flush()


async def any_for(session: AsyncSession, unit_id: uuid.UUID) -> bool:
    stmt = select(UnitBusinessHours.id).where(UnitBusinessHours.unit_id == unit_id).limit(1)
    return (await session.execute(stmt)).first() is not None
