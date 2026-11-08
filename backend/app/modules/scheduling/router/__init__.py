"""HTTP routes of the scheduling module, one file per resource. Thin: the service decides."""

from app.modules.scheduling.router import schedules, time_off, working_time

routers = [schedules.router, time_off.router, working_time.router]
