"""Rules shared by the unit, hours and calendar-exception services (spec S01)."""

from __future__ import annotations

import uuid
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFound, UnprocessableEntity
from app.modules.identity.dependencies import AuthContext
from app.modules.identity.model import Unit, UnitExceptionKind
from app.modules.identity.repository import units as unit_repo

UNIT_NOT_FOUND = "Unidade não encontrada"
NAME_TAKEN = "Já existe uma unidade com esse nome"

# New units open Monday to Saturday, 09:00–19:00 (T6): no agenda is born empty.
DEFAULT_WEEK: list[tuple[int, time, time]] = [(wd, time(9), time(19)) for wd in range(1, 7)]
MAX_EXCEPTION_DAYS = 366


async def visible_unit(session: AsyncSession, ctx: AuthContext, unit_id: uuid.UUID) -> Unit:
    """A unit the user is linked to (or any, for whole-shop users); otherwise 404."""
    unit = await unit_repo.get(session, unit_id)
    if unit is None or (ctx.unit_filter is not None and unit.id not in ctx.unit_filter):
        raise NotFound(UNIT_NOT_FOUND)
    return unit


async def configurable_unit(session: AsyncSession, ctx: AuthContext, unit_id: uuid.UUID) -> Unit:
    """
    A unit the caller may configure: `ctx` comes from `require(UNIT_CONFIGURE)`,
    so its scope is resolved — the owner reaches every unit, a manager only theirs.
    Out of reach looks like not found.
    """
    unit = await unit_repo.get(session, unit_id)
    if unit is None or not ctx.reaches_unit(unit.id):
        raise NotFound(UNIT_NOT_FOUND)
    return unit


def unit_today(unit: Unit) -> date:
    return datetime.now(ZoneInfo(unit.timezone)).date()


def check_exception(
    *,
    starts_on: date,
    ends_on: date,
    kind: UnitExceptionKind,
    opens_at: time | None,
    closes_at: time | None,
    today: date,
) -> None:
    """The rules of one calendar exception, for a new one or the result of a patch."""
    if ends_on < starts_on:
        raise UnprocessableEntity("A data final deve ser igual ou depois da inicial")
    if (ends_on - starts_on).days + 1 > MAX_EXCEPTION_DAYS:
        raise UnprocessableEntity("Uma exceção cobre no máximo 366 dias")
    if ends_on < today:
        raise UnprocessableEntity("Data no passado")
    if kind is UnitExceptionKind.CLOSED:
        if opens_at is not None or closes_at is not None:
            raise UnprocessableEntity("Dia fechado não tem horário")
    elif opens_at is None or closes_at is None:
        raise UnprocessableEntity("Informe o horário especial de abertura e fechamento")
    elif opens_at >= closes_at:
        raise UnprocessableEntity("O horário de abertura deve ser antes do fechamento")
