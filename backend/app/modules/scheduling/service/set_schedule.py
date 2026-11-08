from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnprocessableEntity
from app.modules.identity.public import AuthContext
from app.modules.scheduling.repository import work_hours as hours_repo
from app.modules.scheduling.schemas import BarberScheduleOut, WeeklyScheduleIn
from app.modules.scheduling.service._scope import reach_barber
from app.modules.scheduling.service.get_schedule import schedule_out

EMPTY_WEEK = (
    "A jornada precisa de pelo menos um dia de trabalho. Para afastar o barbeiro, registre uma "
    "ausência ou inative o cadastro"
)


async def set_schedule(
    session: AsyncSession, ctx: AuthContext, barber_id: uuid.UUID, data: WeeklyScheduleIn
) -> BarberScheduleOut:
    """
    Replace the weekly schedule (`team:manage`). It applies to the whole future
    (T4); appointments left outside are highlighted by the agenda. Intervals
    outside the unit's hours are accepted with a warning — the effective time
    is the intersection.
    """
    barber = await reach_barber(session, ctx, barber_id)
    rows = [(d.weekday, i.starts_at, i.ends_at) for d in data.days for i in d.intervals]
    if not rows:
        raise UnprocessableEntity(EMPTY_WEEK)
    await hours_repo.replace(session, barber.id, rows)
    return await schedule_out(session, barber)
