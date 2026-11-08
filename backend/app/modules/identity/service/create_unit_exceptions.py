from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequest, Conflict, NotFound
from app.modules.identity.dependencies import AuthContext
from app.modules.identity.model import UnitException
from app.modules.identity.schemas import UnitExceptionIn
from app.modules.identity.service._unit_rules import check_exception, configurable_unit, unit_today

OVERLAP = "Já existe uma exceção nesse período nesta unidade"


async def create_unit_exceptions(
    session: AsyncSession, ctx: AuthContext, data: UnitExceptionIn
) -> list[UnitException]:
    """
    One exception per unit, all in one transaction (`unit:configure`): any
    unit unknown or out of reach → 400 and nothing is created. A closure on a
    day that already has appointments is allowed (Q-S01-3); the agenda
    highlights them.
    """
    created: list[UnitException] = []
    for unit_id in dict.fromkeys(data.unit_ids):  # de-duplicated, order kept
        try:
            unit = await configurable_unit(session, ctx, unit_id)
        except NotFound as exc:
            raise BadRequest("Unidade inválida ou fora do seu acesso") from exc
        check_exception(
            starts_on=data.starts_on,
            ends_on=data.ends_on,
            kind=data.kind,
            opens_at=data.opens_at,
            closes_at=data.closes_at,
            today=unit_today(unit),
        )
        exception = UnitException(
            unit_id=unit.id,
            starts_on=data.starts_on,
            ends_on=data.ends_on,
            kind=data.kind,
            opens_at=data.opens_at,
            closes_at=data.closes_at,
            reason=data.reason,
            created_by_user_id=ctx.user.id,
        )
        session.add(exception)
        created.append(exception)
    try:
        await session.flush()
    except IntegrityError as exc:  # ex_unit_exception_overlap
        raise Conflict(OVERLAP) from exc
    for exception in created:
        await session.refresh(exception)
    return created
