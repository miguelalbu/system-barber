import enum


class TimeOffKind(enum.StrEnum):
    """Whole days off (`day_off`, `vacation`, `sick_leave`) or a `block` within one day."""

    DAY_OFF = "day_off"
    VACATION = "vacation"
    SICK_LEAVE = "sick_leave"
    BLOCK = "block"

    @property
    def all_day(self) -> bool:
        return self is not TimeOffKind.BLOCK
