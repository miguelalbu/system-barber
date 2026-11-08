from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.dependencies import AuthContext
from app.modules.identity.model import Unit
from app.modules.identity.service._unit_rules import visible_unit


async def get_unit(session: AsyncSession, ctx: AuthContext, unit_id: uuid.UUID) -> Unit:
    return await visible_unit(session, ctx, unit_id)
