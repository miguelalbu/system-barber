"""
Barbers' weekly schedule and special shifts (spec S02). Reading is
`appointment:read` (a barber sees only their own); changing is `team:manage`.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.modules.identity.public import AuthContext, Permission, SessionDep, require
from app.modules.scheduling.schemas import (
    BarberScheduleOut,
    ShiftOverrideIn,
    ShiftOverrideOut,
    WeeklyScheduleIn,
)
from app.modules.scheduling.service.delete_shift_override import delete_shift_override
from app.modules.scheduling.service.get_schedule import get_schedule
from app.modules.scheduling.service.list_schedules import list_schedules
from app.modules.scheduling.service.list_shift_overrides import list_shift_overrides
from app.modules.scheduling.service.set_schedule import set_schedule
from app.modules.scheduling.service.set_shift_override import set_shift_override

router = APIRouter(tags=["scheduling"])

ReadAgenda = Annotated[AuthContext, Depends(require(Permission.APPOINTMENT_READ))]
ManageTeam = Annotated[AuthContext, Depends(require(Permission.TEAM_MANAGE))]


@router.get("/schedules", response_model=list[BarberScheduleOut], summary="Schedule grid")
async def schedules(
    ctx: ReadAgenda, session: SessionDep, unit_id: uuid.UUID | None = None
) -> list[BarberScheduleOut]:
    """One row per active barber in reach."""
    return await list_schedules(session, ctx, unit_id=unit_id)


@router.get(
    "/barbers/{barber_id}/schedule", response_model=BarberScheduleOut, summary="Weekly schedule"
)
async def schedule(barber_id: uuid.UUID, ctx: ReadAgenda, session: SessionDep) -> BarberScheduleOut:
    """`configured: false` → no schedule saved; the unit's hours apply."""
    return await get_schedule(session, ctx, barber_id)


@router.put(
    "/barbers/{barber_id}/schedule", response_model=BarberScheduleOut, summary="Replace the week"
)
async def replace_schedule(
    barber_id: uuid.UUID, data: WeeklyScheduleIn, ctx: ManageTeam, session: SessionDep
) -> BarberScheduleOut:
    """7 days, 0–3 intervals each (lunch is the gap). A whole empty week is refused."""
    return await set_schedule(session, ctx, barber_id, data)


@router.get(
    "/barbers/{barber_id}/shift-overrides",
    response_model=list[ShiftOverrideOut],
    summary="Special shifts",
)
async def shift_overrides(
    barber_id: uuid.UUID,
    ctx: ReadAgenda,
    session: SessionDep,
    from_: Annotated[date | None, Query(alias="from")] = None,
    to: date | None = None,
) -> list[ShiftOverrideOut]:
    return await list_shift_overrides(session, ctx, barber_id, start=from_, end=to)


@router.put(
    "/barbers/{barber_id}/shift-overrides/{on_date}",
    response_model=ShiftOverrideOut,
    summary="Special shift on a day",
)
async def put_shift_override(
    barber_id: uuid.UUID, on_date: date, data: ShiftOverrideIn, ctx: ManageTeam, session: SessionDep
) -> ShiftOverrideOut:
    """Replaces the weekly schedule on that day only; never opens the unit."""
    return await set_shift_override(session, ctx, barber_id, on_date, data)


@router.delete(
    "/barbers/{barber_id}/shift-overrides/{on_date}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Back to the weekly schedule",
)
async def remove_shift_override(
    barber_id: uuid.UUID, on_date: date, ctx: ManageTeam, session: SessionDep
) -> None:
    await delete_shift_override(session, ctx, barber_id, on_date)
