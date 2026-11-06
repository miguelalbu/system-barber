from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.dependencies import AuthContext
from app.modules.identity.model import Unit
from app.modules.identity.repository import units as unit_repo


async def list_units(session: AsyncSession, ctx: AuthContext) -> list[Unit]:
    """Units the user can see, active or not."""
    return await unit_repo.list_visible(session, unit_ids=ctx.unit_filter)
