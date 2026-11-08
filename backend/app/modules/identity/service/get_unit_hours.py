from __future__ import annotations

import uuid
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.dependencies import AuthContext
from app.modules.identity.repository import unit_hours as hours_repo
from app.modules.identity.schemas import DayHours, Interval, WeeklyHoursOut
from app.modules.identity.service._unit_rules import visible_unit

NO_HOURS_WARNING = "Unidade sem nenhum horário de funcionamento"


async def weekly_hours_out(session: AsyncSession, unit_id: uuid.UUID) -> WeeklyHoursOut:
    by_day: dict[int, list[Interval]] = defaultdict(list)
    for row in await hours_repo.list_for(session, [unit_id]):
        by_day[row.weekday].append(Interval(opens_at=row.opens_at, closes_at=row.closes_at))
    days = [DayHours(weekday=wd, intervals=by_day[wd]) for wd in range(1, 8)]
    warning = None if any(d.intervals for d in days) else NO_HOURS_WARNING
    return WeeklyHoursOut(unit_id=unit_id, days=days, warning=warning)


async def get_unit_hours(
    session: AsyncSession, ctx: AuthContext, unit_id: uuid.UUID
) -> WeeklyHoursOut:
    unit = await visible_unit(session, ctx, unit_id)
    return await weekly_hours_out(session, unit.id)
