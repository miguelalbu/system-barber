"""Request and response contracts of the identity module."""

from __future__ import annotations

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.modules.identity.model.enums import Role, TenantStatus

SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])$")

RESERVED_SLUGS = {"www", "app", "api", "admin", "painel", "static", "assets"}


class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# Provisioning
# --------------------------------------------------------------------------- #


class RegisterShop(BaseModel):
    shop_name: str = Field(min_length=2, max_length=120)
    slug: str = Field(min_length=3, max_length=63)
    unit_name: str = Field(default="Unidade principal", max_length=120)

    owner_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("slug")
    @classmethod
    def _valid_slug(cls, v: str) -> str:
        v = v.lower().strip()
        if not SLUG_RE.match(v):
            raise ValueError(
                "slug deve ter 3+ caracteres, só letras minúsculas, números e hífen, "
                "sem começar nem terminar com hífen"
            )
        if v in RESERVED_SLUGS:
            raise ValueError("slug reservado")
        return v


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


class RegistrationOut(BaseModel):
    tenant: TenantOut
    user: UserOut
    tokens: TokensOut
    panel_url: str


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
