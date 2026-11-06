from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.dependencies import AuthContext
from app.modules.identity.permissions import permissions_for
from app.modules.identity.repository import units as unit_repo
from app.modules.identity.schemas import MeOut


async def get_profile(session: AsyncSession, ctx: AuthContext) -> MeOut:
    """Who is signed in, in which shop, which units they see and what they may do."""
    units = await unit_repo.list_visible(session, unit_ids=ctx.unit_filter, active_only=True)
    return MeOut(
        user=ctx.user,
        tenant=ctx.tenant,
        barber_id=ctx.barber_id,
        units=units,
        all_units=ctx.all_units,
        permissions=permissions_for(ctx.role),
    )
