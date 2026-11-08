from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.dependencies import AuthContext
from app.modules.identity.model import Unit
from app.modules.identity.repository import units as unit_repo


async def list_units(
    session: AsyncSession, ctx: AuthContext, *, active: bool | None = None
) -> list[Unit]:
    """Units the user can see, optionally only active or only inactive ones."""
    units = await unit_repo.list_visible(session, unit_ids=ctx.unit_filter)
    return [u for u in units if active is None or u.active is active]
