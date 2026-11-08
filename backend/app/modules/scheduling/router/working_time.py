"""Effective working time of a unit's barbers (spec S02) — what the agenda builds on."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.modules.identity.public import AuthContext, Permission, SessionDep, require
from app.modules.scheduling.schemas import WorkingTimeOut
from app.modules.scheduling.service.get_working_time import get_working_time

router = APIRouter(tags=["scheduling"])

ReadAgenda = Annotated[AuthContext, Depends(require(Permission.APPOINTMENT_READ))]


@router.get("/working-time", response_model=WorkingTimeOut, summary="Effective working time")
async def working_time(
    ctx: ReadAgenda,
    session: SessionDep,
    unit_id: uuid.UUID,
    from_: Annotated[date, Query(alias="from")],
    to: date,
) -> WorkingTimeOut:
    """Schedule ∩ unit hours − time off, per day, in UTC. Up to 31 days."""
    return await get_working_time(session, ctx, unit_id=unit_id, start=from_, end=to)
