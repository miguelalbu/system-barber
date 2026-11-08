from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnprocessableEntity
from app.modules.identity.public import AuthContext
from app.modules.scheduling.schemas import (
    BarberWorkingTime,
    TimeOffRef,
    UtcInterval,
    WorkingDay,
    WorkingTimeOut,
)
from app.modules.scheduling.service._scope import visible_barbers
from app.modules.scheduling.service.working_time import effective_intervals, unit_timezone

MAX_DAYS = 31


async def get_working_time(
    session: AsyncSession, ctx: AuthContext, *, unit_id: uuid.UUID, start: date, end: date
) -> WorkingTimeOut:
    """Effective working time of the unit's active barbers in reach, day by day, in UTC."""
    if end < start or (end - start).days + 1 > MAX_DAYS:
        raise UnprocessableEntity(f"Período inválido (até {MAX_DAYS} dias)")
    tz = await unit_timezone(session, unit_id)
    barbers = await visible_barbers(session, ctx, unit_id=unit_id)
    work = await effective_intervals(session, barbers, start, end)
    return WorkingTimeOut(
        timezone=tz.key,
        barbers=[
            BarberWorkingTime(
                barber_id=b.id,
                days=[
                    WorkingDay(
                        date=d.date,
                        intervals=[UtcInterval(starts_at=s, ends_at=e) for s, e in d.intervals],
                        source=d.source,
                        time_off=[
                            TimeOffRef(
                                id=t.id, kind=t.kind, starts_at=t.starts_at, ends_at=t.ends_at
                            )
                            for t in d.time_off
                        ],
                    )
                    for d in work[b.id].values()
                ],
            )
            for b in barbers
        ],
    )
