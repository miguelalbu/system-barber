from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFound
from app.modules.identity.dependencies import AuthContext
from app.modules.identity.model import Barber
from app.modules.identity.repository import barbers as barber_repo


async def get_barber(session: AsyncSession, ctx: AuthContext, barber_id: uuid.UUID) -> Barber:
    """
    A barber the caller can reach. Outside the caller's units it looks exactly
    like a barber that does not exist. Other modules use this through `public`.
    """
    barber = await barber_repo.get(session, barber_id)
    if barber is None or not ctx.reaches_unit(barber.unit_id):
        raise NotFound("Barbeiro não encontrado")
    return barber
