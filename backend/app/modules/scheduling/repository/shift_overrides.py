import uuid
from collections.abc import Iterable
from datetime import date, time

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.scheduling.model import BarberShiftOverride


async def list_between(
    session: AsyncSession, barber_ids: Iterable[uuid.UUID], start: date, end: date
) -> list[BarberShiftOverride]:
    stmt = (
        select(BarberShiftOverride)
        .where(
            BarberShiftOverride.barber_id.in_(list(barber_ids)),
            BarberShiftOverride.on_date.between(start, end),
        )
        .order_by(BarberShiftOverride.on_date, BarberShiftOverride.starts_at)
    )
    return list((await session.execute(stmt)).scalars())


async def replace_day(
    session: AsyncSession,
    barber_id: uuid.UUID,
    on_date: date,
    rows: Iterable[tuple[time, time]],
    *,
    reason: str | None,
    created_by: uuid.UUID,
) -> None:
    await delete_day(session, barber_id, on_date)
    session.add_all(
        BarberShiftOverride(
            barber_id=barber_id,
            on_date=on_date,
            starts_at=s,
            ends_at=e,
            reason=reason,
            created_by_user_id=created_by,
        )
        for s, e in rows
    )
    await session.flush()


async def delete_day(session: AsyncSession, barber_id: uuid.UUID, on_date: date) -> int:
    result = await session.execute(
        delete(BarberShiftOverride).where(
            BarberShiftOverride.barber_id == barber_id, BarberShiftOverride.on_date == on_date
        )
    )
    return result.rowcount or 0
