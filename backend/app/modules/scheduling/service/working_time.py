"""
Effective working time of barbers, day by day (spec S02):

    (special shift of the day, or weekly schedule, or the unit's hours if the
     barber has no schedule — T2) ∩ the unit's open hours that day (S01)
    − time off and blocks

Computed in the unit's local time, returned in UTC. The agenda (S03) subtracts
appointments from this to find free slots.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import minutes, to_time
from app.modules.identity.public import BarberInfo, get_unit, get_unit_calendar, get_unit_week
from app.modules.scheduling.model import BarberTimeOff
from app.modules.scheduling.repository import shift_overrides as override_repo
from app.modules.scheduling.repository import time_off as time_off_repo
from app.modules.scheduling.repository import work_hours as hours_repo

Minutes = list[tuple[int, int]]
Source = Literal["weekly", "unit_default", "override"]


@dataclass
class DayWork:
    date: date
    intervals: list[tuple[datetime, datetime]]  # UTC
    source: Source
    time_off: list[BarberTimeOff] = field(default_factory=list)

    @property
    def minutes(self) -> int:
        return sum(int((e - s).total_seconds() // 60) for s, e in self.intervals)


def as_minutes(intervals: list[tuple[time, time]]) -> Minutes:
    return sorted((minutes(s), minutes(e) if e != time(23, 59) else 24 * 60) for s, e in intervals)


def intersect(a: Minutes, b: Minutes) -> Minutes:
    out: Minutes = []
    for s1, e1 in a:
        for s2, e2 in b:
            s, e = max(s1, s2), min(e1, e2)
            if s < e:
                out.append((s, e))
    return sorted(out)


def subtract(a: Minutes, b: Minutes) -> Minutes:
    """The parts of `a` not covered by `b`."""
    result = list(a)
    for cs, ce in b:
        nxt: Minutes = []
        for s, e in result:
            if ce <= s or cs >= e:
                nxt.append((s, e))
                continue
            if s < cs:
                nxt.append((s, cs))
            if ce < e:
                nxt.append((ce, e))
        result = nxt
    return sorted(result)


def _subtract_utc(
    intervals: list[tuple[datetime, datetime]], cuts: list[tuple[datetime, datetime]]
) -> list[tuple[datetime, datetime]]:
    result = list(intervals)
    for cs, ce in cuts:
        nxt = []
        for s, e in result:
            if ce <= s or cs >= e:
                nxt.append((s, e))
                continue
            if s < cs:
                nxt.append((s, cs))
            if ce < e:
                nxt.append((ce, e))
        result = nxt
    return sorted(result)


def local_day_bounds(day: date, tz: ZoneInfo) -> tuple[datetime, datetime]:
    """Local midnight of `day` and of the next day, as aware datetimes (DST-safe)."""
    return (
        datetime.combine(day, time(0), tzinfo=tz),
        datetime.combine(day + timedelta(days=1), time(0), tzinfo=tz),
    )


def _to_utc(day: date, span: Minutes, tz: ZoneInfo) -> list[tuple[datetime, datetime]]:
    out = []
    for s, e in span:
        start = datetime.combine(day, to_time(s), tzinfo=tz)
        end = (
            local_day_bounds(day, tz)[1]
            if e >= 24 * 60
            else datetime.combine(day, to_time(e), tzinfo=tz)
        )
        out.append((start.astimezone(ZoneInfo("UTC")), end.astimezone(ZoneInfo("UTC"))))
    return out


async def effective_intervals(
    session: AsyncSession, barbers: list[BarberInfo], start: date, end: date
) -> dict[uuid.UUID, dict[date, DayWork]]:
    """Working time of each barber for every day in [start, end], in UTC."""
    if not barbers:
        return {}
    ids = [b.id for b in barbers]
    weekly: dict[uuid.UUID, dict[int, list[tuple[time, time]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for row in await hours_repo.list_for(session, ids):
        weekly[row.barber_id][row.weekday].append((row.starts_at, row.ends_at))
    overrides: dict[tuple[uuid.UUID, date], list[tuple[time, time]]] = defaultdict(list)
    for row in await override_repo.list_between(session, ids, start, end):
        overrides[(row.barber_id, row.on_date)].append((row.starts_at, row.ends_at))

    calendars = {}
    zones: dict[uuid.UUID, ZoneInfo] = {}
    for unit_id in {b.unit_id for b in barbers}:
        calendars[unit_id] = await get_unit_calendar(session, unit_id, start, end)
        zones[unit_id] = calendars[unit_id].timezone

    # Time off in the whole period, padded a day each side for timezones.
    pad_start = datetime.combine(start - timedelta(days=1), time(0), tzinfo=ZoneInfo("UTC"))
    pad_end = datetime.combine(end + timedelta(days=2), time(0), tzinfo=ZoneInfo("UTC"))
    absences: dict[uuid.UUID, list[BarberTimeOff]] = defaultdict(list)
    for row in await time_off_repo.list_between(
        session, barber_ids=ids, start=pad_start, end=pad_end
    ):
        absences[row.barber_id].append(row)

    result: dict[uuid.UUID, dict[date, DayWork]] = {}
    for barber in barbers:
        calendar, tz = calendars[barber.unit_id], zones[barber.unit_id]
        configured = bool(weekly.get(barber.id))
        days: dict[date, DayWork] = {}
        day = start
        while day <= end:
            unit_open = as_minutes(calendar.days[day])
            if (barber.id, day) in overrides:
                base, source = as_minutes(overrides[(barber.id, day)]), "override"
            elif configured:
                base, source = as_minutes(weekly[barber.id][day.isoweekday()]), "weekly"
            else:
                base, source = unit_open, "unit_default"
            utc = _to_utc(day, intersect(base, unit_open), tz)
            lo, hi = local_day_bounds(day, tz)
            touching = [t for t in absences[barber.id] if t.starts_at < hi and t.ends_at > lo]
            utc = _subtract_utc(utc, [(t.starts_at, t.ends_at) for t in touching])
            days[day] = DayWork(date=day, intervals=utc, source=source, time_off=touching)
            day += timedelta(days=1)
        result[barber.id] = days
    return result


async def unit_timezone(session: AsyncSession, unit_id: uuid.UUID) -> ZoneInfo:
    unit = await get_unit(session, unit_id)
    return ZoneInfo(unit.timezone if unit else "America/Sao_Paulo")


async def unit_week_minutes(session: AsyncSession, unit_id: uuid.UUID) -> dict[int, Minutes]:
    return {wd: as_minutes(iv) for wd, iv in (await get_unit_week(session, unit_id)).items()}
