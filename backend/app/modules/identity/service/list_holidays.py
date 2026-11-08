from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.dependencies import AuthContext
from app.modules.identity.model import UnitExceptionKind
from app.modules.identity.repository import unit_exceptions as exception_repo
from app.modules.identity.repository import units as unit_repo
from app.modules.identity.schemas import HolidayOut
from app.modules.identity.service._holidays import national_holidays


async def list_holidays(session: AsyncSession, ctx: AuthContext, year: int) -> list[HolidayOut]:
    """
    Suggested national holidays of the year and which visible units are already
    closed on each. Nothing closes by itself: the panel creates `closed`
    exceptions for the ones the owner or manager picks.
    """
    units = await unit_repo.list_visible(session, unit_ids=ctx.unit_filter)
    closures = await exception_repo.list_between(
        session,
        unit_ids=[u.id for u in units],
        start=date(year, 1, 1),
        end=date(year, 12, 31),
        kind=UnitExceptionKind.CLOSED,
    )

    def closed_on(day: date) -> list[uuid.UUID]:
        return sorted({c.unit_id for c in closures if c.starts_on <= day <= c.ends_on}, key=str)

    return [
        HolidayOut(date=day, name=name, already_closed_unit_ids=closed_on(day))
        for day, name in national_holidays(year)
    ]
