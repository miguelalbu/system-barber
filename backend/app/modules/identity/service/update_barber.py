from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.dependencies import AuthContext
from app.modules.identity.repository import barbers as barber_repo
from app.modules.identity.schemas import BarberOut, BarberUpdate
from app.modules.identity.service._barber_rules import (
    barber_out,
    check_linkable_user,
    check_unit,
    check_unlinkable,
)
from app.modules.identity.service.get_barber import get_barber


async def update_barber(
    session: AsyncSession, ctx: AuthContext, barber_id: uuid.UUID, data: BarberUpdate
) -> BarberOut:
    barber = await get_barber(session, ctx, barber_id)
    sent = data.model_fields_set

    if data.unit_id is not None and data.unit_id != barber.unit_id:
        await check_unit(session, ctx, data.unit_id)
        barber.unit_id = data.unit_id

    if "user_id" in sent and data.user_id != barber.user_id:
        if barber.user_id is not None:
            await check_unlinkable(session, barber.user_id)
        if data.user_id is not None:
            await check_linkable_user(session, data.user_id, barber_id=barber.id)
        barber.user_id = data.user_id

    if data.name is not None:
        barber.name = data.name
    if data.initials is not None:
        barber.initials = data.initials
    if data.default_commission is not None:
        barber.default_commission = round(data.default_commission, 2)
    if data.active is not None:
        barber.active = data.active

    await session.flush()
    updated = await barber_repo.get(session, barber.id)
    assert updated is not None
    return barber_out(updated)
