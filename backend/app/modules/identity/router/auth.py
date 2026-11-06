"""Login, rotating refresh, logout and /me. Shops are created by the control plane."""

from __future__ import annotations

from fastapi import APIRouter, status

from app.modules.identity.dependencies import CurrentUser, SessionDep, TenantDep
from app.modules.identity.schemas import (
    LoginIn,
    MeOut,
    RefreshIn,
    TokensOut,
)
from app.modules.identity.service.get_profile import get_profile
from app.modules.identity.service.login import login as login_service
from app.modules.identity.service.logout import logout as logout_service
from app.modules.identity.service.refresh_session import refresh_session

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokensOut, summary="Staff login")
async def login(data: LoginIn, tenant: TenantDep, session: SessionDep):
    return await login_service(session, tenant, data)


@router.post("/refresh", response_model=TokensOut, summary="Renew the access token")
async def refresh(data: RefreshIn, tenant: TenantDep, session: SessionDep):
    return await refresh_session(session, tenant, data.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Revoke the refresh token")
async def logout(data: RefreshIn, tenant: TenantDep, session: SessionDep):
    await logout_service(session, data.refresh_token)


@router.get("/me", response_model=MeOut, summary="Current user, shop and permissions")
async def me(ctx: CurrentUser, session: SessionDep):
    return await get_profile(session, ctx)
