"""Data and configuration of the logged-in shop."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.deps import AuthContext, CurrentUser, PlatformSessionDep, SessionDep, require
from app.models import Tenant, Unit
from app.permissions import Permission
from app.schemas import TenantOut, TenantUpdate, UnitOut

router = APIRouter(prefix="/tenant", tags=["shop"])

Configure = Annotated[AuthContext, Depends(require(Permission.TENANT_CONFIGURE))]


@router.get("", response_model=TenantOut, summary="Current shop")
async def current(ctx: CurrentUser) -> Tenant:
    return ctx.tenant


@router.patch("", response_model=TenantOut, summary="Update shop details")
async def update(data: TenantUpdate, ctx: Configure, session: PlatformSessionDep) -> Tenant:
    # `tenants` is control plane and has no RLS, so this session carries no
    # tenant — which is why the query filters by the context id explicitly.
    tenant = (await session.execute(select(Tenant).where(Tenant.id == ctx.tenant.id))).scalar_one()

    if data.name is not None:
        tenant.name = data.name
    if data.custom_domain is not None:
        tenant.custom_domain = data.custom_domain.lower().strip() or None

    try:
        await session.flush()
    except IntegrityError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Esse domínio já está em uso por outra barbearia"
        ) from exc

    return tenant


@router.get("/units", response_model=list[UnitOut], summary="Visible units")
async def units(ctx: CurrentUser, session: SessionDep) -> list[Unit]:
    stmt = select(Unit).order_by(Unit.name)
    if not ctx.all_units:
        stmt = stmt.where(Unit.id.in_(ctx.units))
    return list((await session.execute(stmt)).scalars())
