"""Data and configuration of the logged-in shop."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.modules.identity.dependencies import AuthContext, ControlSessionDep, CurrentUser, require
from app.modules.identity.model import Tenant
from app.modules.identity.permissions import Permission
from app.modules.identity.schemas import TenantOut, TenantUpdate
from app.modules.identity.service.update_tenant import update_tenant

router = APIRouter(prefix="/tenant", tags=["shop"])

Configure = Annotated[AuthContext, Depends(require(Permission.TENANT_CONFIGURE))]


@router.get("", response_model=TenantOut, summary="Current shop")
async def current(ctx: CurrentUser) -> Tenant:
    return ctx.tenant


@router.patch("", response_model=TenantOut, summary="Update shop details")
async def update(data: TenantUpdate, ctx: Configure, session: ControlSessionDep) -> Tenant:
    return await update_tenant(session, ctx.tenant.id, data)
