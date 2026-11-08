from __future__ import annotations

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import Conflict, NotFound
from app.modules.identity.dependencies import AuthContext
from app.modules.identity.model import Unit, UnitException, UnitExceptionKind
from app.modules.identity.repository import unit_exceptions as exception_repo
from app.modules.identity.schemas import UnitExceptionUpdate
from app.modules.identity.service._unit_rules import check_exception, configurable_unit, unit_today
from app.modules.identity.service.create_unit_exceptions import OVERLAP

EXCEPTION_NOT_FOUND = "Exceção não encontrada"
_REQUIRED = {"starts_on", "ends_on", "kind"}


async def get_configurable_exception(
    session: AsyncSession, ctx: AuthContext, exception_id: uuid.UUID
) -> tuple[UnitException, Unit]:
    exception = await exception_repo.get(session, exception_id)
    if exception is None:
        raise NotFound(EXCEPTION_NOT_FOUND)
    try:
        unit = await configurable_unit(session, ctx, exception.unit_id)
    except NotFound as exc:
        raise NotFound(EXCEPTION_NOT_FOUND) from exc
    return exception, unit


async def update_unit_exception(
    session: AsyncSession, ctx: AuthContext, exception_id: uuid.UUID, data: UnitExceptionUpdate
) -> UnitException:
    exception, unit = await get_configurable_exception(session, ctx, exception_id)
    changes = data.model_dump(exclude_unset=True)
    changes = {k: v for k, v in changes.items() if v is not None or k not in _REQUIRED}
    if changes.get("kind") is UnitExceptionKind.CLOSED:
        # Becoming a closed day drops the special hours.
        changes.setdefault("opens_at", None)
        changes.setdefault("closes_at", None)

    merged = {
        f: changes.get(f, getattr(exception, f))
        for f in ("starts_on", "ends_on", "kind", "opens_at", "closes_at")
    }
    check_exception(**merged, today=unit_today(unit))

    for field, value in changes.items():
        setattr(exception, field, value)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise Conflict(OVERLAP) from exc
    return await exception_repo.get(session, exception.id)
