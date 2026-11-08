from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFound, UnprocessableEntity
from app.modules.identity.public import AuthContext
from app.modules.scheduling.repository import shift_overrides as override_repo
from app.modules.scheduling.service._dates import local_today
from app.modules.scheduling.service._scope import reach_barber
from app.modules.scheduling.service.set_shift_override import PAST_DATE
from app.modules.scheduling.service.working_time import unit_timezone


async def delete_shift_override(
    session: AsyncSession, ctx: AuthContext, barber_id: uuid.UUID, on_date: date
) -> None:
    """Back to the weekly schedule on that day."""
    barber = await reach_barber(session, ctx, barber_id)
    if on_date < local_today(await unit_timezone(session, barber.unit_id)):
        raise UnprocessableEntity(PAST_DATE)
    if not await override_repo.delete_day(session, barber.id, on_date):
        raise NotFound("Não há turno especial nessa data")
