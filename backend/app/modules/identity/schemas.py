"""Request and response contracts of the identity module."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

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
    create_barber: bool = Field(
        default=False, description="Also create the calendar column for this user"
    )

    @field_validator("role")
    @classmethod
    def _no_second_owner(cls, v: Role) -> Role:
        if v is Role.OWNER:
            raise ValueError("transfira a propriedade em vez de convidar um segundo dono")
        return v


class InviteOut(Schema):
    id: uuid.UUID
    name: str
    email: EmailStr
    role: Role
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
