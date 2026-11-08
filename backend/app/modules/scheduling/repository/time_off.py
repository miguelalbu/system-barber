import uuid
from collections.abc import Iterable
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.scheduling.model import BarberTimeOff, TimeOffKind


async def get(session: AsyncSession, time_off_id: uuid.UUID) -> BarberTimeOff | None:
    return await session.get(BarberTimeOff, time_off_id, populate_existing=True)


async def list_between(
    session: AsyncSession,
    *,
    barber_ids: Iterable[uuid.UUID],
    start: datetime,
    end: datetime,
    kind: TimeOffKind | None = None,
) -> list[BarberTimeOff]:
    """Time off touching [start, end)."""
    stmt = select(BarberTimeOff).where(
        BarberTimeOff.barber_id.in_(list(barber_ids)),
        BarberTimeOff.starts_at < end,
        BarberTimeOff.ends_at > start,
    )
    if kind is not None:
        stmt = stmt.where(BarberTimeOff.kind == kind)
    return list((await session.execute(stmt.order_by(BarberTimeOff.starts_at))).scalars())
