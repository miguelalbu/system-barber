"""Request and response contracts of the scheduling module."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

from app.core.clock import ClockTime
from app.modules.scheduling.model.enums import TimeOffKind

MAX_INTERVALS = 3


def _blank_to_none(v: object) -> object:
    return None if isinstance(v, str) and not v.strip() else v


class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class WorkInterval(BaseModel):
    starts_at: ClockTime
    ends_at: ClockTime

    @model_validator(mode="after")
    def _ordered(self) -> WorkInterval:
        if self.starts_at >= self.ends_at:
            raise ValueError("o início deve ser antes do fim")
        return self


def check_apart(intervals: list[WorkInterval]) -> list[WorkInterval]:
    """Sorted; no overlap and no touching (same rule as the unit hours)."""
    intervals.sort(key=lambda i: i.starts_at)
    for before, after in zip(intervals, intervals[1:], strict=False):
        if after.starts_at == before.ends_at:
            raise ValueError("junte os intervalos que se encostam")
        if after.starts_at < before.ends_at:
            raise ValueError("os intervalos de um dia não podem se sobrepor")
    return intervals


class WorkDay(BaseModel):
    weekday: int = Field(ge=1, le=7, description="ISO: 1 = Monday … 7 = Sunday")
    intervals: list[WorkInterval] = Field(default_factory=list, max_length=MAX_INTERVALS)

    @model_validator(mode="after")
    def _apart(self) -> WorkDay:
        check_apart(self.intervals)
        return self


class WeeklyScheduleIn(BaseModel):
    days: list[WorkDay] = Field(min_length=7, max_length=7)

    @model_validator(mode="after")
    def _whole_week(self) -> WeeklyScheduleIn:
        if sorted(d.weekday for d in self.days) != list(range(1, 8)):
            raise ValueError("envie os 7 dias da semana, sem repetir")
        self.days.sort(key=lambda d: d.weekday)
        return self


class BarberScheduleOut(BaseModel):
    barber_id: uuid.UUID
    unit_id: uuid.UUID
    configured: bool = Field(description="False: no schedule saved, the unit's hours apply (T2)")
    days: list[WorkDay]
    weekly_minutes: int = Field(description="Effective minutes a week (schedule ∩ unit hours)")
    warnings: list[str] = Field(default_factory=list)


ShiftReason = Annotated[
    Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)] | None,
    BeforeValidator(_blank_to_none),
]


class ShiftOverrideIn(BaseModel):
    intervals: list[WorkInterval] = Field(min_length=1, max_length=MAX_INTERVALS)
    reason: ShiftReason = None

    @model_validator(mode="after")
    def _apart(self) -> ShiftOverrideIn:
        check_apart(self.intervals)
        return self


class ShiftOverrideOut(BaseModel):
    barber_id: uuid.UUID
    date: date
    intervals: list[WorkInterval]
    reason: str | None
    warnings: list[str] = Field(default_factory=list)


TimeOffReason = Annotated[
    Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)] | None,
    BeforeValidator(_blank_to_none),
    Field(description="Staff only; the AI just says the barber is not working"),
]


class TimeOffIn(BaseModel):
    """Whole days: `starts_on`/`ends_on`. Block: `starts_at`/`ends_at` (with offset)."""

    barber_id: uuid.UUID
    kind: TimeOffKind
    starts_on: date | None = None
    ends_on: date | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    reason: TimeOffReason = None


class TimeOffUpdate(BaseModel):
    starts_on: date | None = None
    ends_on: date | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    reason: TimeOffReason = None


class TimeOffOut(BaseModel):
    id: uuid.UUID
    barber_id: uuid.UUID
    kind: TimeOffKind
    all_day: bool
    starts_at: datetime
    ends_at: datetime
    starts_on: date = Field(description="First local day")
    ends_on: date = Field(description="Last local day (inclusive)")
    reason: str | None
    created_by_user_id: uuid.UUID | None
    created_at: datetime


class AffectedAppointment(BaseModel):
    id: uuid.UUID
    starts_at: datetime
    client_name: str


class TimeOffResult(BaseModel):
    time_off: TimeOffOut
    affected_appointments: list[AffectedAppointment] = Field(
        default_factory=list, description="Active appointments in the period (filled by S03)"
    )


class UtcInterval(BaseModel):
    starts_at: datetime
    ends_at: datetime


class TimeOffRef(BaseModel):
    id: uuid.UUID
    kind: TimeOffKind
    starts_at: datetime
    ends_at: datetime


class WorkingDay(BaseModel):
    date: date
    intervals: list[UtcInterval]
    source: Literal["weekly", "unit_default", "override"]
    time_off: list[TimeOffRef]


class BarberWorkingTime(BaseModel):
    barber_id: uuid.UUID
    days: list[WorkingDay]


class WorkingTimeOut(BaseModel):
    timezone: str
    barbers: list[BarberWorkingTime]
