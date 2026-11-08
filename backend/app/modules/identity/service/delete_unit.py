from __future__ import annotations

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import Conflict, NotFound
from app.modules.identity.repository import units as unit_repo
from app.modules.identity.service._unit_rules import UNIT_NOT_FOUND
from app.modules.identity.service.update_unit import LAST_ACTIVE_UNIT

HAS_HISTORY = "Esta unidade tem histórico; inative em vez de apagar"
HAS_USER_LINKS = "Há usuários com acesso a esta unidade; ajuste em Equipe antes"


async def delete_unit(session: AsyncSession, unit_id: uuid.UUID) -> None:
    """
    Delete for real only without history (DEC-016 P1): barbers and, later,
    appointments point at it with `RESTRICT`, so the database refuses → 409.
    Hours and exceptions go with it. A unit linked to users is refused too: the
    cascade would turn a user restricted to it into one who sees every unit.
    """
    unit = await unit_repo.get(session, unit_id)
    if unit is None:
        raise NotFound(UNIT_NOT_FOUND)
    if unit.active and await unit_repo.count_active(session, exclude_id=unit.id) == 0:
        raise Conflict(LAST_ACTIVE_UNIT)
    if await unit_repo.has_user_links(session, unit.id):
        raise Conflict(HAS_USER_LINKS)

    await session.delete(unit)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise Conflict(HAS_HISTORY) from exc
