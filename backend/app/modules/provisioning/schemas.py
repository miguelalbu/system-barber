"""Contracts of the control plane (`/core/*`). Served only behind `X-Core-Key`."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.modules.identity.public import InvalidSlug, TenantStatus, validate_slug
from app.modules.provisioning.model import JobStatus, JobStep


class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class OwnerIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr


class ProvisionIn(BaseModel):
    """
    Unknown fields are dropped — on purpose for `password`: the owner's password
    never travels in this contract (doc §6) and never reaches the audit log.
    """

    model_config = ConfigDict(extra="ignore")

    slug: str = Field(description="Subdomain and schema of the shop: <slug>.<base_domain>")
    name: str = Field(min_length=2, max_length=120)
    owner: OwnerIn
    unit_name: str | None = Field(default=None, max_length=120)
    plan: str = Field(default="basic", max_length=40)
    custom_domain: str | None = Field(default=None, max_length=255)
    external_tenant_id: str | None = Field(
        default=None, max_length=120, description="The Core's id for this customer"
    )

    @field_validator("slug")
    @classmethod
    def _valid_slug(cls, v: str) -> str:
        try:
            return validate_slug(v)
        except InvalidSlug as exc:
            raise ValueError(str(exc)) from exc

    @field_validator("custom_domain")
    @classmethod
    def _normalize_domain(cls, v: str | None) -> str | None:
        return v.strip().lower() or None if v else None


class ProvisionAccepted(BaseModel):
    tenant_id: uuid.UUID
    status: TenantStatus
    job_id: uuid.UUID


class JobOut(Schema):
    id: uuid.UUID
    status: JobStatus
    step: JobStep
    log: str
    error: str | None
    created_at: datetime
    finished_at: datetime | None


class CoreTenantOut(Schema):
    id: uuid.UUID
    slug: str
    schema_name: str
    name: str
    custom_domain: str | None
    plan: str
    status: TenantStatus
    schema_version: str | None
    external_tenant_id: str | None
    created_at: datetime


class CoreTenantDetail(CoreTenantOut):
    job: JobOut | None = None
    invite_link: str | None = Field(
        default=None,
        description="Owner's first-access link. Delivered once, then erased.",
    )


class InviteLinkOut(BaseModel):
    invite_link: str


class DestroyIn(BaseModel):
    confirm: str = Field(description="The shop's slug, typed again")
    exported: bool = Field(description="A pg_dump of the schema was taken")
