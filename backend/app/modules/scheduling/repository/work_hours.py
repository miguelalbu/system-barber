import uuid
from collections.abc import Iterable
from datetime import time

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.scheduling.model import BarberWorkHours


async def list_for(session: AsyncSession, barber_ids: Iterable[uuid.UUID]) -> list[BarberWorkHours]:
    stmt = (
        select(BarberWorkHours)
        .where(BarberWorkHours.barber_id.in_(list(barber_ids)))
        .order_by(BarberWorkHours.weekday, BarberWorkHours.starts_at)
    )
    return list((await session.execute(stmt)).scalars())


async def replace(
    session: AsyncSession, barber_id: uuid.UUID, rows: Iterable[tuple[int, time, time]]
) -> None:
    await session.execute(delete(BarberWorkHours).where(BarberWorkHours.barber_id == barber_id))
    session.add_all(
        BarberWorkHours(barber_id=barber_id, weekday=wd, starts_at=s, ends_at=e)
        for wd, s, e in rows
    )
    await session.flush()


async def configured_ids(session: AsyncSession, barber_ids: Iterable[uuid.UUID]) -> set[uuid.UUID]:
    stmt = (
        select(BarberWorkHours.barber_id)
        .where(BarberWorkHours.barber_id.in_(list(barber_ids)))
        .distinct()
    )
    return set((await session.execute(stmt)).scalars())
