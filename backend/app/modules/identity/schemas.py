"""Request and response contracts of the identity module."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Annotated
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from app.core.clock import ClockTime
from app.core.phone import normalize_phone
from app.modules.identity.model.enums import Role, TenantStatus, UnitExceptionKind


class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# Shop
# --------------------------------------------------------------------------- #


class TenantOut(Schema):
    id: uuid.UUID
    slug: str
    name: str
    custom_domain: str | None
    plan: str
    status: TenantStatus
    created_at: datetime


class TenantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    custom_domain: str | None = Field(default=None, max_length=255)


# --------------------------------------------------------------------------- #
# Authentication
# --------------------------------------------------------------------------- #


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RefreshIn(BaseModel):
    refresh_token: str


class TokensOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token lifetime, in seconds")


class UnitOut(Schema):
    id: uuid.UUID
    name: str
    timezone: str
    address: str | None
    phone: str | None = Field(description="E.164")
    online_booking: bool = Field(description="Offered to the AI and the public booking link")
    active: bool
    created_at: datetime
    updated_at: datetime


class UserOut(Schema):
    id: uuid.UUID
    name: str
    email: EmailStr
    role: Role
    active: bool
    last_login_at: datetime | None


class MeOut(BaseModel):
    user: UserOut
    tenant: TenantOut
    barber_id: uuid.UUID | None
    units: list[UnitOut]
    all_units: bool
    permissions: dict[str, str]


# --------------------------------------------------------------------------- #
# Team
# --------------------------------------------------------------------------- #


class InviteIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    role: Role
    unit_ids: list[uuid.UUID] = Field(
        default_factory=list, description="Empty means access to every unit"
    )
    barber_id: uuid.UUID | None = Field(
        default=None,
        description=(
            "Registered barber this login is linked to on acceptance. Required for the "
            "`barber` role; an invite never creates a barber."
        ),
    )

    @field_validator("role")
    @classmethod
    def _no_second_owner(cls, v: Role) -> Role:
        if v is Role.OWNER:
            raise ValueError("transfira a propriedade em vez de convidar um segundo dono")
        return v

    @model_validator(mode="after")
    def _barber_role_needs_a_barber(self) -> InviteIn:
        if self.role is Role.BARBER and self.barber_id is None:
            raise ValueError("Escolha o barbeiro cadastrado")
        return self


class InviteOut(Schema):
    id: uuid.UUID
    name: str
    email: EmailStr
    role: Role
    barber_id: uuid.UUID | None
    expires_at: datetime
    accepted_at: datetime | None
    created_at: datetime


class InviteCreatedOut(BaseModel):
    invite: InviteOut
    # Until transactional email exists, the link comes back in the response so
    # the owner can forward it over WhatsApp. See README, "Pendências".
    link: str


class AcceptInviteIn(BaseModel):
    token: str
    password: str = Field(min_length=8, max_length=128)


class MemberOut(Schema):
    id: uuid.UUID
    name: str
    email: EmailStr
    role: Role
    active: bool
    last_login_at: datetime | None
    barber_id: uuid.UUID | None = None


class InviteLookupIn(BaseModel):
    token: str


class InviteLookupOut(Schema):
    """What the acceptance page shows before asking for a password."""

    name: str
    email: EmailStr
    role: Role
    expires_at: datetime


# --------------------------------------------------------------------------- #
# Barbers — the scheduling resource, a registry separate from logins
# --------------------------------------------------------------------------- #

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=120)]
Initials = Annotated[
    str, StringConstraints(strip_whitespace=True, to_upper=True, min_length=1, max_length=4)
]
Commission = Annotated[float, Field(ge=0, le=100)]


class BarberIn(BaseModel):
    name: Name
    unit_id: uuid.UUID
    initials: Initials | None = Field(default=None, description="Derived from the name if omitted")
    default_commission: Commission = 40
    active: bool = True
    user_id: uuid.UUID | None = Field(
        default=None, description="Existing login to link (e.g. an owner who also cuts)"
    )


class BarberUpdate(BaseModel):
    """Partial: a field left out does not change. `user_id: null` unlinks the login."""

    name: Name | None = None
    unit_id: uuid.UUID | None = None
    initials: Initials | None = None
    default_commission: Commission | None = None
    active: bool | None = None
    user_id: uuid.UUID | None = None


class BarberOut(BaseModel):
    id: uuid.UUID
    name: str
    initials: str
    unit_id: uuid.UUID
    default_commission: float
    active: bool
    user_id: uuid.UUID | None
    email: EmailStr | None = Field(description="Email of the linked login, if any")
    created_at: datetime
    updated_at: datetime


# --------------------------------------------------------------------------- #
# Units, opening hours, calendar exceptions, shop settings (spec S01)
# --------------------------------------------------------------------------- #


def _blank_to_none(v: object) -> object:
    return None if isinstance(v, str) and not v.strip() else v


def _valid_timezone(v: str) -> str:
    try:
        ZoneInfo(v)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError("Fuso horário inválido") from exc
    return v


def _instagram(v: str) -> str:
    v = v.lstrip("@")
    if not v or any(c.isspace() for c in v):
        raise ValueError("informe só o usuário do Instagram, sem espaços")
    return v


Timezone = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=64),
    AfterValidator(_valid_timezone),
    Field(description="IANA timezone, e.g. America/Sao_Paulo"),
]
OptionalText300 = Annotated[
    Annotated[str, StringConstraints(strip_whitespace=True, max_length=300)] | None,
    BeforeValidator(_blank_to_none),
]
OptionalPhone = Annotated[
    Annotated[
        str,
        StringConstraints(strip_whitespace=True, max_length=32),
        AfterValidator(normalize_phone),
    ]
    | None,
    BeforeValidator(_blank_to_none),
    Field(description="Any common format; stored and returned in E.164"),
]


class UnitIn(BaseModel):
    name: Name
    timezone: Timezone = "America/Sao_Paulo"
    address: OptionalText300 = None
    phone: OptionalPhone = None
    online_booking: bool = True
    active: bool = True


class UnitUpdate(BaseModel):
    """Partial. `null` clears address and phone; for the other fields it means no change."""

    name: Name | None = None
    timezone: Timezone | None = None
    address: OptionalText300 = None
    phone: OptionalPhone = None
    online_booking: bool | None = None
    active: bool | None = None


class Interval(BaseModel):
    opens_at: ClockTime
    closes_at: ClockTime

    @model_validator(mode="after")
    def _ordered(self) -> Interval:
        if self.opens_at >= self.closes_at:
            raise ValueError("o horário de abertura deve ser antes do fechamento")
        return self


class DayHours(BaseModel):
    weekday: int = Field(ge=1, le=7, description="ISO: 1 = Monday … 7 = Sunday")
    intervals: list[Interval] = Field(default_factory=list, max_length=3)

    @model_validator(mode="after")
    def _apart(self) -> DayHours:
        self.intervals.sort(key=lambda i: i.opens_at)
        for before, after in zip(self.intervals, self.intervals[1:], strict=False):
            if after.opens_at == before.closes_at:
                raise ValueError("junte os intervalos que se encostam")
            if after.opens_at < before.closes_at:
                raise ValueError("os intervalos de um dia não podem se sobrepor")
        return self


class WeeklyHoursIn(BaseModel):
    days: list[DayHours] = Field(min_length=7, max_length=7)

    @model_validator(mode="after")
    def _whole_week(self) -> WeeklyHoursIn:
        if sorted(d.weekday for d in self.days) != list(range(1, 8)):
            raise ValueError("envie os 7 dias da semana, sem repetir")
        self.days.sort(key=lambda d: d.weekday)
        return self


class WeeklyHoursOut(BaseModel):
    unit_id: uuid.UUID
    days: list[DayHours]
    warning: str | None = None


ExceptionReason = Annotated[
    Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)] | None,
    BeforeValidator(_blank_to_none),
    Field(description="Shown to clients by the AI, e.g. 'feriado de Finados'"),
]


class UnitExceptionIn(BaseModel):
    unit_ids: list[uuid.UUID] = Field(min_length=1, description="One exception per unit")
    starts_on: date
    ends_on: date
    kind: UnitExceptionKind
    opens_at: ClockTime | None = Field(default=None, description="Only for special_hours")
    closes_at: ClockTime | None = Field(default=None, description="Only for special_hours")
    reason: ExceptionReason = None


class UnitExceptionUpdate(BaseModel):
    """Partial; the merged result is checked with the same rules as a new one."""

    starts_on: date | None = None
    ends_on: date | None = None
    kind: UnitExceptionKind | None = None
    opens_at: ClockTime | None = None
    closes_at: ClockTime | None = None
    reason: ExceptionReason = None


class UnitExceptionOut(Schema):
    id: uuid.UUID
    unit_id: uuid.UUID
    starts_on: date
    ends_on: date
    kind: UnitExceptionKind
    opens_at: ClockTime | None
    closes_at: ClockTime | None
    reason: str | None
    created_at: datetime
    updated_at: datetime


class HolidayOut(BaseModel):
    date: date
    name: str
    already_closed_unit_ids: list[uuid.UUID] = Field(
        description="Visible units already closed on this date"
    )


Instagram = Annotated[
    Annotated[
        str, StringConstraints(strip_whitespace=True, max_length=61), AfterValidator(_instagram)
    ]
    | None,
    BeforeValidator(_blank_to_none),
]
About = Annotated[
    Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)] | None,
    BeforeValidator(_blank_to_none),
]


def _quarter_hour(v: int | None) -> int | None:
    if v is not None and v % 15:
        raise ValueError("use múltiplos de 15 minutos")
    return v


MinAdvance = Annotated[int, Field(ge=0, le=2880), AfterValidator(_quarter_hour)]


class ShopSettingsOut(Schema):
    contact_phone: str | None
    instagram: str | None
    about: str | None
    min_advance_minutes: int = Field(description="Client channels only; the staff has no limit")
    max_advance_days: int
    confirmation_deadline_hours: int
    client_change_min_hours: int
    late_tolerance_minutes: int
    max_future_appointments_per_client: int
    barber_sees_client_contact: bool
    updated_at: datetime


class ShopSettingsUpdate(BaseModel):
    """Partial. `null` clears the contact fields; for a policy it means no change."""

    contact_phone: OptionalPhone = None
    instagram: Instagram = None
    about: About = None
    min_advance_minutes: MinAdvance | None = None
    max_advance_days: int | None = Field(default=None, ge=1, le=180)
    confirmation_deadline_hours: int | None = Field(default=None, ge=1, le=48)
    client_change_min_hours: int | None = Field(default=None, ge=0, le=72)
    late_tolerance_minutes: int | None = Field(default=None, ge=0, le=60)
    max_future_appointments_per_client: int | None = Field(default=None, ge=1, le=20)
    barber_sees_client_contact: bool | None = None
