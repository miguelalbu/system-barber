from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import Conflict, NotFound, UnprocessableEntity
from app.modules.identity.public import AuthContext
from app.modules.scheduling.model import BarberTimeOff
from app.modules.scheduling.repository import time_off as time_off_repo
from app.modules.scheduling.schemas import TimeOffResult, TimeOffUpdate
from app.modules.scheduling.service._scope import BARBER_NOT_FOUND, reach_barber
from app.modules.scheduling.service._time_off_rules import (
    OVERLAP,
    authorize,
    local_dates,
    resolve,
    to_out,
)
from app.modules.scheduling.service.working_time import unit_timezone

TIME_OFF_NOT_FOUND = "Ausência não encontrada"


async def reachable_time_off(
    session: AsyncSession, ctx: AuthContext, time_off_id: uuid.UUID
) -> tuple[BarberTimeOff, uuid.UUID]:
    """The record and its barber's unit, with the permission of its kind; else 403/404."""
    row = await time_off_repo.get(session, time_off_id)
    if row is None:
        raise NotFound(TIME_OFF_NOT_FOUND)
    ctx = authorize(ctx, row.kind)
    try:
        barber = await reach_barber(session, ctx, row.barber_id)
    except NotFound as exc:
        raise NotFound(TIME_OFF_NOT_FOUND if str(exc) == BARBER_NOT_FOUND else str(exc)) from exc
    return row, barber.unit_id


async def update_time_off(
    session: AsyncSession, ctx: AuthContext, time_off_id: uuid.UUID, data: TimeOffUpdate
) -> TimeOffResult:
    row, unit_id = await reachable_time_off(session, ctx, time_off_id)
    if row.ends_at <= datetime.now(UTC):
        raise UnprocessableEntity("Ausência passada não pode ser editada")
    tz = await unit_timezone(session, unit_id)
    sent = data.model_fields_set
    if row.kind.all_day:
        first, last = local_dates(row, tz)
        starts_at, ends_at = resolve(
            row.kind,
            tz,
            starts_on=data.starts_on if "starts_on" in sent else first,
            ends_on=data.ends_on if "ends_on" in sent else last,
            starts_at=data.starts_at,
            ends_at=data.ends_at,
        )
    else:
        starts_at, ends_at = resolve(
            row.kind,
            tz,
            starts_on=data.starts_on,
            ends_on=data.ends_on,
            starts_at=data.starts_at if "starts_at" in sent else row.starts_at,
            ends_at=data.ends_at if "ends_at" in sent else row.ends_at,
        )
    row.starts_at, row.ends_at = starts_at, ends_at
    if "reason" in sent:
        row.reason = data.reason
    try:
        await session.flush()
    except IntegrityError as exc:
        raise Conflict(OVERLAP) from exc
    return TimeOffResult(time_off=to_out(await time_off_repo.get(session, row.id), tz))
