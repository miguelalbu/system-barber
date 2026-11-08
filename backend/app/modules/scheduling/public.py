"""
The only surface other modules may import from scheduling.

Reports (S14) read capacity; onboarding (S16) asks which barbers have no
schedule. The agenda (S03) lives in this module and uses the services directly.
"""

from app.modules.scheduling.service.capacity import barbers_without_hours, capacity_minutes

__all__ = ["barbers_without_hours", "capacity_minutes"]
