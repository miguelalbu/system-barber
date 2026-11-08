from __future__ import annotations

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import Conflict, NotFound
from app.modules.identity.model import Unit
from app.modules.identity.repository import units as unit_repo
from app.modules.identity.schemas import UnitUpdate
from app.modules.identity.service._unit_rules import NAME_TAKEN, UNIT_NOT_FOUND

LAST_ACTIVE_UNIT = "A barbearia precisa de pelo menos uma unidade ativa"
HAS_ACTIVE_BARBERS = "Mova ou inative os barbeiros desta unidade antes"

# Columns that cannot be null: sending `null` for them means "no change".
_REQUIRED = {"name", "timezone", "online_booking", "active"}


async def update_unit(session: AsyncSession, unit_id: uuid.UUID, data: UnitUpdate) -> Unit:
    """
    Partial update (owner only, `tenant:configure`). Changing the timezone moves
    nothing stored in UTC — the panel warns that local times of future
    appointments change. Reactivating is where the plan limit (S15) will be checked.
    """
    unit = await unit_repo.get(session, unit_id)
    if unit is None:
        raise NotFound(UNIT_NOT_FOUND)

    changes = data.model_dump(exclude_unset=True)
    changes = {k: v for k, v in changes.items() if v is not None or k not in _REQUIRED}
    if "name" in changes and await unit_repo.name_taken(
        session, changes["name"], exclude_id=unit.id
    ):
        raise Conflict(NAME_TAKEN)
    if unit.active and changes.get("active") is False:
        if await unit_repo.count_active(session, exclude_id=unit.id) == 0:
            raise Conflict(LAST_ACTIVE_UNIT)
        if await unit_repo.has_active_barbers(session, unit.id):
            raise Conflict(HAS_ACTIVE_BARBERS)

    for field, value in changes.items():
        setattr(unit, field, value)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise Conflict(NAME_TAKEN) from exc
    return await unit_repo.get(session, unit.id)
