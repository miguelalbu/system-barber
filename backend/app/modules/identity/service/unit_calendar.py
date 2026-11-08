"""
Read-only views of units and policies for other modules (spec S01) — the agenda
(S02, S03), the AI (S11) and the booking link (S04) build on these through
`identity.public`, never on the tables.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFound
from app.modules.identity.model import UnitExceptionKind
from app.modules.identity.repository import shop_settings as settings_repo
from app.modules.identity.repository import unit_exceptions as exception_repo
from app.modules.identity.repository import unit_hours as hours_repo
from app.modules.identity.repository import units as unit_repo
from app.modules.identity.service._unit_rules import UNIT_NOT_FOUND

MAX_CALENDAR_DAYS = 400


@dataclass(frozen=True)
class UnitInfo:
    id: uuid.UUID
    name: str
    timezone: str
    online_booking: bool
    active: bool


@dataclass(frozen=True)
class UnitCalendar:
    """
    Effective opening of a unit, day by day, in its own timezone: weekly hours
    with the exceptions applied. A day with no interval is closed;
    `closed_reason` has the days closed by an exception (reason may be None).
    """

    unit_id: uuid.UUID
    timezone: ZoneInfo
    days: dict[date, list[tuple[time, time]]]
    closed_reason: dict[date, str | None]


@dataclass(frozen=True)
class ShopPolicies:
    contact_phone: str | None
    instagram: str | None
    about: str | None
    min_advance_minutes: int
    max_advance_days: int
    confirmation_deadline_hours: int
    client_change_min_hours: int
    late_tolerance_minutes: int
    max_future_appointments_per_client: int
    barber_sees_client_contact: bool


def _info(unit) -> UnitInfo:
    return UnitInfo(
        id=unit.id,
        name=unit.name,
        timezone=unit.timezone,
        online_booking=unit.online_booking,
        active=unit.active,
    )


async def unit_info(session: AsyncSession, unit_id: uuid.UUID) -> UnitInfo | None:
    unit = await unit_repo.get(session, unit_id)
    return None if unit is None else _info(unit)


async def list_unit_infos(
    session: AsyncSession, *, active_only: bool = True, online_only: bool = False
) -> list[UnitInfo]:
    units = await unit_repo.list_visible(session, unit_ids=None, active_only=active_only)
    return [_info(u) for u in units if u.online_booking or not online_only]


async def unit_week(
    session: AsyncSession, unit_id: uuid.UUID
) -> dict[int, list[tuple[time, time]]]:
    """The unit's regular week (ISO weekday → intervals), without exceptions."""
    weekly: dict[int, list[tuple[time, time]]] = {wd: [] for wd in range(1, 8)}
    for row in await hours_repo.list_for(session, [unit_id]):
        weekly[row.weekday].append((row.opens_at, row.closes_at))
    return weekly


async def unit_calendar(
    session: AsyncSession, unit_id: uuid.UUID, start: date, end: date
) -> UnitCalendar:
    if end < start or (end - start).days >= MAX_CALENDAR_DAYS:
        raise ValueError("calendar range must be 1 to 400 days")
    unit = await unit_repo.get(session, unit_id)
    if unit is None:
        raise NotFound(UNIT_NOT_FOUND)

    weekly: dict[int, list[tuple[time, time]]] = defaultdict(list)
    for row in await hours_repo.list_for(session, [unit.id]):
        weekly[row.weekday].append((row.opens_at, row.closes_at))
    exceptions = await exception_repo.list_between(
        session, unit_ids=[unit.id], start=start, end=end
    )

    days: dict[date, list[tuple[time, time]]] = {}
    closed_reason: dict[date, str | None] = {}
    day = start
    while day <= end:
        exception = next((e for e in exceptions if e.starts_on <= day <= e.ends_on), None)
        if exception is None:
            days[day] = list(weekly[day.isoweekday()])
        elif exception.kind is UnitExceptionKind.CLOSED:
            days[day] = []
            closed_reason[day] = exception.reason
        else:
            days[day] = [(exception.opens_at, exception.closes_at)]
        day += timedelta(days=1)
    return UnitCalendar(
        unit_id=unit.id, timezone=ZoneInfo(unit.timezone), days=days, closed_reason=closed_reason
    )


async def shop_policies(session: AsyncSession) -> ShopPolicies:
    row = await settings_repo.get_or_create(session)
    return ShopPolicies(**{f: getattr(row, f) for f in ShopPolicies.__dataclass_fields__})
