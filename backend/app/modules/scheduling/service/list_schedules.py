from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.public import AuthContext
from app.modules.scheduling.schemas import BarberScheduleOut
from app.modules.scheduling.service._scope import visible_barbers
from app.modules.scheduling.service.get_schedule import schedule_out


async def list_schedules(
    session: AsyncSession, ctx: AuthContext, *, unit_id: uuid.UUID | None
) -> list[BarberScheduleOut]:
    """The schedule grid: one row per active barber in reach."""
    barbers = await visible_barbers(session, ctx, unit_id=unit_id)
    return [await schedule_out(session, b) for b in barbers]
