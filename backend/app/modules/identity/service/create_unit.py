from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import Conflict
from app.modules.identity.model import Unit
from app.modules.identity.repository import unit_hours as hours_repo
from app.modules.identity.repository import units as unit_repo
from app.modules.identity.schemas import UnitIn
from app.modules.identity.service._unit_rules import DEFAULT_WEEK, NAME_TAKEN


async def create_unit(session: AsyncSession, data: UnitIn) -> Unit:
    """
    A new unit, born with the default week (T6). The plan's unit limit (S15)
    is checked here once that spec exists; until then there is no limit.
    """
    if await unit_repo.name_taken(session, data.name):
        raise Conflict(NAME_TAKEN)
    unit = Unit(**data.model_dump())
    session.add(unit)
    try:
        await session.flush()
    except IntegrityError as exc:  # same name created concurrently
        raise Conflict(NAME_TAKEN) from exc
    await hours_repo.replace(session, unit.id, DEFAULT_WEEK)
    return await unit_repo.get(session, unit.id)
