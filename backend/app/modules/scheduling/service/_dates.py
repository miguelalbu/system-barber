"""Date helpers in the unit's timezone."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo


def local_today(tz: ZoneInfo) -> date:
    return datetime.now(tz).date()
