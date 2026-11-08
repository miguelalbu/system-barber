from __future__ import annotations

import uuid
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import to_time
from app.modules.identity.public import AuthContext, BarberInfo
from app.modules.scheduling.repository import work_hours as hours_repo
from app.modules.scheduling.schemas import BarberScheduleOut, WorkDay, WorkInterval
from app.modules.scheduling.service._scope import reach_barber
from app.modules.scheduling.service.working_time import (
    Minutes,
    as_minutes,
    intersect,
    subtract,
    unit_week_minutes,
)

WEEKDAY_NAMES = {
    1: "Segunda",
    2: "Terça",
    3: "Quarta",
    4: "Quinta",
    5: "Sexta",
    6: "Sábado",
    7: "Domingo",
}


def _fmt(m: int) -> str:
    return to_time(m).strftime("%H:%M") if m < 24 * 60 else "24:00"


def outside_warnings(label: str, wanted: Minutes, open_: Minutes) -> list[str]:
    """'Terça 19:00–20:00 fica fora do horário da unidade', one per uncovered piece."""
    return [
        f"{label} {_fmt(s)}–{_fmt(e)} fica fora do horário da unidade"
        for s, e in subtract(wanted, open_)
    ]


async def schedule_out(session: AsyncSession, barber: BarberInfo) -> BarberScheduleOut:
    rows = await hours_repo.list_for(session, [barber.id])
    unit_week = await unit_week_minutes(session, barber.unit_id)
    by_day: dict[int, Minutes] = defaultdict(list)
    for row in rows:
        by_day[row.weekday].extend(as_minutes([(row.starts_at, row.ends_at)]))
    configured = bool(rows)
    week = {wd: (sorted(by_day[wd]) if configured else unit_week[wd]) for wd in range(1, 8)}

    warnings: list[str] = []
    total = 0
    for wd in range(1, 8):
        total += sum(e - s for s, e in intersect(week[wd], unit_week[wd]))
        if configured:
            warnings += outside_warnings(WEEKDAY_NAMES[wd], week[wd], unit_week[wd])
    days = [
        WorkDay(
            weekday=wd,
            intervals=[WorkInterval(starts_at=to_time(s), ends_at=to_time(e)) for s, e in week[wd]],
        )
        for wd in range(1, 8)
    ]
    return BarberScheduleOut(
        barber_id=barber.id,
        unit_id=barber.unit_id,
        configured=configured,
        days=days,
        weekly_minutes=total,
        warnings=warnings,
    )


async def get_schedule(
    session: AsyncSession, ctx: AuthContext, barber_id: uuid.UUID
) -> BarberScheduleOut:
    return await schedule_out(session, await reach_barber(session, ctx, barber_id))
