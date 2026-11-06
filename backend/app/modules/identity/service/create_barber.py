from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.dependencies import AuthContext
from app.modules.identity.model import Barber
from app.modules.identity.repository import barbers as barber_repo
from app.modules.identity.schemas import BarberIn, BarberOut
from app.modules.identity.service._barber_rules import (
    barber_out,
    check_linkable_user,
    check_unit,
    initials_of,
)


async def create_barber(session: AsyncSession, ctx: AuthContext, data: BarberIn) -> BarberOut:
    """
    Register a professional. Never creates a login: access to the panel is a
    separate registry (Team), linked here only when `user_id` is given.
    """
    await check_unit(session, ctx, data.unit_id)
    if data.user_id is not None:
        await check_linkable_user(session, data.user_id)

    barber = Barber(
        name=data.name,
        initials=data.initials or initials_of(data.name),
        unit_id=data.unit_id,
        default_commission=round(data.default_commission, 2),
        active=data.active,
        user_id=data.user_id,
    )
    session.add(barber)
    await session.flush()

    created = await barber_repo.get(session, barber.id)
    assert created is not None
    return barber_out(created)
