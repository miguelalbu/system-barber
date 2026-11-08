from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import Conflict
from app.modules.identity.public import AuthContext
from app.modules.scheduling.model import BarberTimeOff
from app.modules.scheduling.repository import time_off as time_off_repo
from app.modules.scheduling.schemas import TimeOffIn, TimeOffResult
from app.modules.scheduling.service._scope import reach_barber
from app.modules.scheduling.service._time_off_rules import OVERLAP, authorize, resolve, to_out
from app.modules.scheduling.service.working_time import unit_timezone


async def create_time_off(
    session: AsyncSession, ctx: AuthContext, data: TimeOffIn
) -> TimeOffResult:
    """
    Allowed over existing appointments (T5): they stay booked and the response
    lists them so the panel can warn (filled once the agenda, S03, exists).
    """
    ctx = authorize(ctx, data.kind)
    barber = await reach_barber(session, ctx, data.barber_id)
    tz = await unit_timezone(session, barber.unit_id)
    starts_at, ends_at = resolve(
        data.kind,
        tz,
        starts_on=data.starts_on,
        ends_on=data.ends_on,
        starts_at=data.starts_at,
        ends_at=data.ends_at,
    )
    row = BarberTimeOff(
        barber_id=barber.id,
        kind=data.kind,
        all_day=data.kind.all_day,
        starts_at=starts_at,
        ends_at=ends_at,
        reason=data.reason,
        created_by_user_id=ctx.user.id,
    )
    session.add(row)
    try:
        await session.flush()
    except IntegrityError as exc:  # ex_time_off_overlap
        raise Conflict(OVERLAP) from exc
    return TimeOffResult(time_off=to_out(await time_off_repo.get(session, row.id), tz))
