"""
Time off (day off, vacation, sick leave — whole days, `team:manage`) and blocks
(a range in one day, `appointment:create`: also the front desk and the barber
on their own column) — spec S02.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.modules.identity.public import AuthContext, CurrentUser, Permission, SessionDep, require
from app.modules.scheduling.model import TimeOffKind
from app.modules.scheduling.schemas import TimeOffIn, TimeOffOut, TimeOffResult, TimeOffUpdate
from app.modules.scheduling.service.create_time_off import create_time_off
from app.modules.scheduling.service.delete_time_off import delete_time_off
from app.modules.scheduling.service.list_time_off import list_time_off
from app.modules.scheduling.service.update_time_off import update_time_off

router = APIRouter(prefix="/time-off", tags=["scheduling"])

ReadAgenda = Annotated[AuthContext, Depends(require(Permission.APPOINTMENT_READ))]


@router.get("", response_model=list[TimeOffOut], summary="Time off and blocks in a period")
async def time_off(
    ctx: ReadAgenda,
    session: SessionDep,
    from_: Annotated[date, Query(alias="from")],
    to: date,
    unit_id: uuid.UUID | None = None,
    barber_id: uuid.UUID | None = None,
    kind: TimeOffKind | None = None,
) -> list[TimeOffOut]:
    """Up to 366 days."""
    return await list_time_off(
        session, ctx, start=from_, end=to, unit_id=unit_id, barber_id=barber_id, kind=kind
    )


@router.post(
    "", response_model=TimeOffResult, status_code=status.HTTP_201_CREATED, summary="Add time off"
)
async def create(data: TimeOffIn, ctx: CurrentUser, session: SessionDep) -> TimeOffResult:
    """Permission depends on the kind. Overlap with another one of the barber → 409."""
    return await create_time_off(session, ctx, data)


@router.patch("/{time_off_id}", response_model=TimeOffResult, summary="Edit time off")
async def update(
    time_off_id: uuid.UUID, data: TimeOffUpdate, ctx: CurrentUser, session: SessionDep
) -> TimeOffResult:
    return await update_time_off(session, ctx, time_off_id, data)


@router.delete("/{time_off_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove time off")
async def delete(time_off_id: uuid.UUID, ctx: CurrentUser, session: SessionDep) -> None:
    """A past block stays (it records why the slot was empty)."""
    await delete_time_off(session, ctx, time_off_id)
