"""Which barbers the caller reaches, under the scope resolved by `require(...)`."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFound
from app.modules.identity.public import (
    AuthContext,
    BarberInfo,
    Scope,
    get_barber_info,
    list_barber_infos,
)

BARBER_NOT_FOUND = "Barbeiro não encontrado"


def reaches(ctx: AuthContext, barber: BarberInfo) -> bool:
    if ctx.scope is Scope.OWN:
        return barber.id == ctx.barber_id
    return ctx.reaches_unit(barber.unit_id)


async def reach_barber(session: AsyncSession, ctx: AuthContext, barber_id: uuid.UUID) -> BarberInfo:
    """A barber in the caller's reach; outside it looks like one that does not exist."""
    barber = await get_barber_info(session, barber_id)
    if barber is None or not reaches(ctx, barber):
        raise NotFound(BARBER_NOT_FOUND)
    return barber


async def visible_barbers(
    session: AsyncSession,
    ctx: AuthContext,
    *,
    unit_id: uuid.UUID | None = None,
    include_inactive: bool = False,
) -> list[BarberInfo]:
    """Barbers in reach (active only unless asked), optionally of one unit."""
    barbers = await list_barber_infos(
        session, unit_ids=ctx.scoped_units, active=None if include_inactive else True
    )
    return [b for b in barbers if reaches(ctx, b) and (unit_id is None or b.unit_id == unit_id)]
