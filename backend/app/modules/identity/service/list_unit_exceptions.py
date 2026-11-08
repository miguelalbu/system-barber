from __future__ import annotations

import uuid
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.dependencies import AuthContext
from app.modules.identity.model import UnitException
from app.modules.identity.repository import unit_exceptions as exception_repo
from app.modules.identity.service._unit_rules import visible_unit


async def list_unit_exceptions(
    session: AsyncSession,
    ctx: AuthContext,
    *,
    unit_id: uuid.UUID | None,
    start: date | None,
    end: date | None,
) -> list[UnitException]:
    """Exceptions of the visible units touching the period (default: today to +365 days)."""
    start = start or date.today()
    end = end or start + timedelta(days=365)
    unit_ids = ctx.unit_filter
    if unit_id is not None:
        unit_ids = [(await visible_unit(session, ctx, unit_id)).id]
    return await exception_repo.list_between(session, unit_ids=unit_ids, start=start, end=end)
