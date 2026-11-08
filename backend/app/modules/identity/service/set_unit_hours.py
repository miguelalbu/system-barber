from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.dependencies import AuthContext
from app.modules.identity.repository import unit_hours as hours_repo
from app.modules.identity.schemas import WeeklyHoursIn, WeeklyHoursOut
from app.modules.identity.service._unit_rules import configurable_unit
from app.modules.identity.service.get_unit_hours import weekly_hours_out


async def set_unit_hours(
    session: AsyncSession, ctx: AuthContext, unit_id: uuid.UUID, data: WeeklyHoursIn
) -> WeeklyHoursOut:
    """
    Replace the whole week (`unit:configure`). Existing appointments are not
    touched; the agenda (S03) highlights the ones left outside the new hours.
    """
    unit = await configurable_unit(session, ctx, unit_id)
    rows = [(d.weekday, i.opens_at, i.closes_at) for d in data.days for i in d.intervals]
    await hours_repo.replace(session, unit.id, rows)
    return await weekly_hours_out(session, unit.id)
