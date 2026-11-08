from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.public import AuthContext
from app.modules.scheduling.repository import shift_overrides as override_repo
from app.modules.scheduling.schemas import ShiftOverrideOut, WorkInterval
from app.modules.scheduling.service._scope import reach_barber


async def list_shift_overrides(
    session: AsyncSession,
    ctx: AuthContext,
    barber_id: uuid.UUID,
    *,
    start: date | None,
    end: date | None,
) -> list[ShiftOverrideOut]:
    """Special shifts of a barber (default: today to 90 days ahead), one per date."""
    barber = await reach_barber(session, ctx, barber_id)
    start = start or date.today()
    end = end or start + timedelta(days=90)
    by_date: dict[date, list] = defaultdict(list)
    for row in await override_repo.list_between(session, [barber.id], start, end):
        by_date[row.on_date].append(row)
    return [
        ShiftOverrideOut(
            barber_id=barber.id,
            date=day,
            intervals=[WorkInterval(starts_at=r.starts_at, ends_at=r.ends_at) for r in rows],
            reason=rows[0].reason,
        )
        for day, rows in sorted(by_date.items())
    ]
