from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnprocessableEntity
from app.modules.identity.public import AuthContext
from app.modules.scheduling.model import TimeOffKind
from app.modules.scheduling.repository import time_off as time_off_repo
from app.modules.scheduling.schemas import TimeOffOut
from app.modules.scheduling.service._scope import reach_barber, visible_barbers
from app.modules.scheduling.service._time_off_rules import local_dates, to_out
from app.modules.scheduling.service.working_time import unit_timezone

MAX_RANGE_DAYS = 366


async def list_time_off(
    session: AsyncSession,
    ctx: AuthContext,
    *,
    start: date,
    end: date,
    unit_id: uuid.UUID | None,
    barber_id: uuid.UUID | None,
    kind: TimeOffKind | None,
) -> list[TimeOffOut]:
    """Time off touching [start, end] (local dates of each barber's unit), in reach."""
    if end < start or (end - start).days + 1 > MAX_RANGE_DAYS:
        raise UnprocessableEntity("Período inválido (até 366 dias)")
    if barber_id is not None:
        barbers = [await reach_barber(session, ctx, barber_id)]
    else:
        barbers = await visible_barbers(session, ctx, unit_id=unit_id, include_inactive=True)
    if not barbers:
        return []

    zones = {u: await unit_timezone(session, u) for u in {b.unit_id for b in barbers}}
    tz_of = {b.id: zones[b.unit_id] for b in barbers}
    # A day of padding each side covers any timezone; exact dates are checked below.
    rows = await time_off_repo.list_between(
        session,
        barber_ids=list(tz_of),
        start=datetime.combine(start - timedelta(days=1), time(0), tzinfo=UTC),
        end=datetime.combine(end + timedelta(days=2), time(0), tzinfo=UTC),
        kind=kind,
    )
    out = []
    for row in rows:
        first, last = local_dates(row, tz_of[row.barber_id])
        if first <= end and last >= start:
            out.append(to_out(row, tz_of[row.barber_id]))
    return out
