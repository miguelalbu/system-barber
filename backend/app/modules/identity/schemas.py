"""Request and response contracts of the identity module."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from app.modules.identity.model.enums import Role, TenantStatus


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
    active: bool


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
