"""
Scheduling tables (per shop, `TenantBase`). Barbers live in identity
(DEC-007, re-evaluated and kept): these point at `barbers.id`.

Importing this package registers every table; `app/core/model_registry.py`
relies on that.
"""

from app.modules.scheduling.model.enums import TimeOffKind
from app.modules.scheduling.model.shift_override import BarberShiftOverride
from app.modules.scheduling.model.time_off import BarberTimeOff
from app.modules.scheduling.model.work_hours import BarberWorkHours

__all__ = ["BarberShiftOverride", "BarberTimeOff", "BarberWorkHours", "TimeOffKind"]
