"""
Wall-clock time of day as the API exchanges it: "HH:MM", five-minute steps,
no timezone (the unit's timezone gives it meaning). Shared by unit hours (S01)
and barber schedules (S02).
"""

from __future__ import annotations

from datetime import time
from typing import Annotated

from pydantic import AfterValidator
from pydantic.functional_serializers import PlainSerializer
from pydantic.json_schema import WithJsonSchema


def _five_minutes(v: time) -> time:
    if v.second or v.microsecond or v.minute % 5:
        raise ValueError("use horários de 5 em 5 minutos")
    return v.replace(tzinfo=None)


ClockTime = Annotated[
    time,
    AfterValidator(_five_minutes),
    PlainSerializer(lambda t: t.strftime("%H:%M"), return_type=str, when_used="json"),
    WithJsonSchema({"type": "string", "pattern": "^[0-2][0-9]:[0-5][0-9]$", "examples": ["09:00"]}),
]


def minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def to_time(total_minutes: int) -> time:
    """Minutes since midnight → time; 1440 (end of day) is clamped to 23:59."""
    if total_minutes >= 24 * 60:
        return time(23, 59)
    return time(total_minutes // 60, total_minutes % 60)
