"""Read-only numbers other modules ask of the barbers' working time (S14, S16)."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.public import list_barber_infos
from app.modules.scheduling.repository import work_hours as hours_repo
from app.modules.scheduling.service.working_time import effective_intervals


async def capacity_minutes(
    session: AsyncSession,
    *,
    unit_id: uuid.UUID,
    start: date,
    end: date,
    barber_ids: list[uuid.UUID] | None = None,
    by_day: bool = False,
) -> dict:
    """
    Effective working minutes (schedule − time off − closures) of the unit's
    active barbers: `{barber_id: minutes}`, or `{(barber_id, date): minutes}`.
    """
    barbers = [
        b
        for b in await list_barber_infos(session, unit_ids=[unit_id], active=True)
        if barber_ids is None or b.id in barber_ids
    ]
    work = await effective_intervals(session, barbers, start, end)
    if by_day:
        return {(bid, day): w.minutes for bid, days in work.items() for day, w in days.items()}
    return {bid: sum(w.minutes for w in days.values()) for bid, days in work.items()}


async def barbers_without_hours(session: AsyncSession) -> list[uuid.UUID]:
    """Active barbers with no schedule saved (they follow the unit's hours, T2)."""
    barbers = await list_barber_infos(session, active=True)
    configured = await hours_repo.configured_ids(session, [b.id for b in barbers])
    return [b.id for b in barbers if b.id not in configured]
