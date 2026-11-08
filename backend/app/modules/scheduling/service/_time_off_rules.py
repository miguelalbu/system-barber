"""Rules of time off and blocks (spec S02): who may, what a valid period is, how it is shown."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.core.exceptions import UnprocessableEntity
from app.modules.identity.public import AuthContext, Permission, require
from app.modules.scheduling.model import BarberTimeOff, TimeOffKind
from app.modules.scheduling.schemas import TimeOffOut

MAX_WHOLE_DAYS = 180
OVERLAP = "Já existe uma ausência nesse horário"
ENDS_IN_THE_PAST = "A ausência termina no passado"
_TICK = timedelta(microseconds=1)


def authorize(ctx: AuthContext, kind: TimeOffKind) -> AuthContext:
    """
    Days off, vacation and sick leave are management's (`team:manage`); a block
    is `appointment:create` — the front desk, and a barber on their own column
    (Q-S02-3). Resolves the scope on `ctx` or raises 403.
    """
    permission = (
        Permission.APPOINTMENT_CREATE if kind is TimeOffKind.BLOCK else Permission.TEAM_MANAGE
    )
    return require(permission)(ctx)


def whole_days(
    starts_on: date | None, ends_on: date | None, tz: ZoneInfo
) -> tuple[datetime, datetime]:
    """Local midnight of the first day to local midnight after the last (T3)."""
    if starts_on is None or ends_on is None:
        raise UnprocessableEntity("Informe o primeiro e o último dia")
    if ends_on < starts_on:
        raise UnprocessableEntity("O último dia deve ser igual ou depois do primeiro")
    if (ends_on - starts_on).days + 1 > MAX_WHOLE_DAYS:
        raise UnprocessableEntity(f"No máximo {MAX_WHOLE_DAYS} dias por ausência")
    return (
        datetime.combine(starts_on, time(0), tzinfo=tz).astimezone(UTC),
        datetime.combine(ends_on + timedelta(days=1), time(0), tzinfo=tz).astimezone(UTC),
    )


def block_range(
    starts_at: datetime | None, ends_at: datetime | None, tz: ZoneInfo
) -> tuple[datetime, datetime]:
    """A block lives inside one local day, up to 24 h, in five-minute steps."""
    if starts_at is None or ends_at is None:
        raise UnprocessableEntity("Informe o início e o fim do bloqueio")
    if starts_at.tzinfo is None or ends_at.tzinfo is None:
        raise UnprocessableEntity("Informe o horário com o fuso (ex.: 2026-11-10T15:00:00-03:00)")
    if ends_at <= starts_at:
        raise UnprocessableEntity("O fim deve ser depois do início")
    if ends_at - starts_at > timedelta(hours=24):
        raise UnprocessableEntity("Um bloqueio dura no máximo 24 horas")
    for moment in (starts_at, ends_at):
        local = moment.astimezone(tz)
        if local.second or local.microsecond or local.minute % 5:
            raise UnprocessableEntity("Use horários de 5 em 5 minutos")
    if starts_at.astimezone(tz).date() != (ends_at - _TICK).astimezone(tz).date():
        raise UnprocessableEntity("O bloqueio precisa caber num único dia")
    return starts_at.astimezone(UTC), ends_at.astimezone(UTC)


def resolve(
    kind: TimeOffKind,
    tz: ZoneInfo,
    *,
    starts_on: date | None,
    ends_on: date | None,
    starts_at: datetime | None,
    ends_at: datetime | None,
) -> tuple[datetime, datetime]:
    if kind.all_day:
        if starts_at is not None or ends_at is not None:
            raise UnprocessableEntity(
                "Folga, férias e atestado são dias inteiros: informe as datas"
            )
        start, end = whole_days(starts_on, ends_on, tz)
    else:
        if starts_on is not None or ends_on is not None:
            raise UnprocessableEntity("Bloqueio é de horário: informe início e fim")
        start, end = block_range(starts_at, ends_at, tz)
    if end <= datetime.now(UTC):
        raise UnprocessableEntity(ENDS_IN_THE_PAST)
    return start, end


def local_dates(row: BarberTimeOff, tz: ZoneInfo) -> tuple[date, date]:
    return row.starts_at.astimezone(tz).date(), (row.ends_at - _TICK).astimezone(tz).date()


def to_out(row: BarberTimeOff, tz: ZoneInfo) -> TimeOffOut:
    starts_on, ends_on = local_dates(row, tz)
    return TimeOffOut(
        id=row.id,
        barber_id=row.barber_id,
        kind=row.kind,
        all_day=row.all_day,
        starts_at=row.starts_at,
        ends_at=row.ends_at,
        starts_on=starts_on,
        ends_on=ends_on,
        reason=row.reason,
        created_by_user_id=row.created_by_user_id,
        created_at=row.created_at,
    )
