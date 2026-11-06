from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.dependencies import AuthContext
from app.modules.identity.repository import barbers as barber_repo
from app.modules.identity.schemas import BarberOut
from app.modules.identity.service._barber_rules import barber_out


async def list_barbers(
    session: AsyncSession,
    ctx: AuthContext,
    *,
    unit_id: uuid.UUID | None = None,
    active: bool | None = None,
) -> list[BarberOut]:
    barbers = await barber_repo.list_visible(
        session, unit_ids=ctx.scoped_units, unit_id=unit_id, active=active
    )
    return [barber_out(b) for b in barbers]
