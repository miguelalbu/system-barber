from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnprocessableEntity
from app.modules.identity.public import AuthContext, get_unit_calendar
from app.modules.scheduling.repository import shift_overrides as override_repo
from app.modules.scheduling.schemas import ShiftOverrideIn, ShiftOverrideOut, WorkInterval
from app.modules.scheduling.service._dates import local_today
from app.modules.scheduling.service._scope import reach_barber
from app.modules.scheduling.service.get_schedule import outside_warnings
from app.modules.scheduling.service.working_time import as_minutes

PAST_DATE = "Data no passado"


async def set_shift_override(
    session: AsyncSession,
    ctx: AuthContext,
    barber_id: uuid.UUID,
    on_date: date,
    data: ShiftOverrideIn,
) -> ShiftOverrideOut:
    """
    A special shift replaces the weekly schedule on that day only (`team:manage`).
    It never opens the unit: outside its hours that day is a warning (Q-S02-2).
    """
    barber = await reach_barber(session, ctx, barber_id)
    calendar = await get_unit_calendar(session, barber.unit_id, on_date, on_date)
    if on_date < local_today(calendar.timezone):
        raise UnprocessableEntity(PAST_DATE)
    rows = [(i.starts_at, i.ends_at) for i in data.intervals]
    await override_repo.replace_day(
        session, barber.id, on_date, rows, reason=data.reason, created_by=ctx.user.id
    )
    label = on_date.strftime("%d/%m")
    return ShiftOverrideOut(
        barber_id=barber.id,
        date=on_date,
        intervals=[WorkInterval(starts_at=s, ends_at=e) for s, e in rows],
        reason=data.reason,
        warnings=outside_warnings(label, as_minutes(rows), as_minutes(calendar.days[on_date])),
    )
