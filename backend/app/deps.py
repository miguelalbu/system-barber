"""
FastAPI dependencies: tenant resolution, database session and authorization.

The chain is always the same, in this order:

    Host → Tenant → session with RLS pinned → user from the JWT → permission
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import SessionFactory, set_tenant
from app.models import Role, Tenant, TenantStatus, User, UserUnit
from app.permissions import Permission, Scope, scope_for
from app.security import InvalidToken, TokenType, decode_token

# --------------------------------------------------------------------------- #
# Tenant from the domain
# --------------------------------------------------------------------------- #


def _hostname(request: Request) -> str:
    host = request.headers.get("host", "")
    return host.split(":")[0].lower().strip()


async def resolve_tenant(
    request: Request,
    x_tenant_slug: Annotated[str | None, Header()] = None,
) -> Tenant:
    """
    Find the shop from the access domain:

    * `central.navalha.app`            → slug `central`
    * `agenda.barbeariacentral.com.br` → the `custom_domain` column

    In development it also accepts the `X-Tenant-Slug` header, so the API can be
    exercised with curl without editing /etc/hosts. In production the header is
    ignored — the tenant must **never** come from something the client picks
    freely.
    """
    host = _hostname(request)
    slug: str | None = None

    if settings.dev and x_tenant_slug:
        slug = x_tenant_slug.lower().strip()
    elif host.endswith(f".{settings.base_domain}"):
        slug = host[: -len(settings.base_domain) - 1]

    async with SessionFactory() as session:
        async with session.begin():
            await set_tenant(session, None)  # control plane table, no RLS
            stmt = (
                select(Tenant).where(Tenant.slug == slug)
                if slug
                else select(Tenant).where(Tenant.custom_domain == host)
            )
            tenant = (await session.execute(stmt)).scalar_one_or_none()

    if tenant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Barbearia não encontrada para '{host}'")
    if tenant.status in (TenantStatus.SUSPENDED, TenantStatus.CANCELED):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Assinatura inativa")

    request.state.tenant = tenant
    return tenant


TenantDep = Annotated[Tenant, Depends(resolve_tenant)]


async def get_session(tenant: TenantDep) -> AsyncIterator[AsyncSession]:
    """Session with the tenant already pinned — from here on RLS handles isolation."""
    async with SessionFactory() as session:
        async with session.begin():
            await set_tenant(session, tenant.id)
            yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_platform_session() -> AsyncIterator[AsyncSession]:
    """For control plane routes (shop signup, invite acceptance)."""
    async with SessionFactory() as session:
        async with session.begin():
            await set_tenant(session, None)
            yield session


PlatformSessionDep = Annotated[AsyncSession, Depends(get_platform_session)]


# --------------------------------------------------------------------------- #
# Authenticated user
# --------------------------------------------------------------------------- #


@dataclass
class AuthContext:
    """Who is calling, from where, and how far they reach."""

    user: User
    tenant: Tenant
    role: Role
    barber_id: uuid.UUID | None
    units: list[uuid.UUID] = field(default_factory=list)
    scope: Scope = Scope.ALL

    @property
    def all_units(self) -> bool:
        """An empty list means access to the whole shop."""
        return not self.units


def _bearer(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Credenciais ausentes",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return authorization[7:].strip()


async def current_user(
    tenant: TenantDep,
    session: SessionDep,
    authorization: Annotated[str | None, Header()] = None,
) -> AuthContext:
    token = _bearer(authorization)
    try:
        payload = decode_token(token)
    except InvalidToken as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc

    if payload.get("typ") != TokenType.ACCESS.value:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Tipo de token incorreto")

    # A token issued for another shop never works here, even though we signed it.
    if payload.get("tid") != str(tenant.id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Token de outra barbearia")

    user = await session.get(User, uuid.UUID(payload["sub"]))
    if user is None or not user.active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuário inativo ou inexistente")

    units = list(
        (
            await session.execute(
                select(UserUnit.unit_id).where(UserUnit.user_id == user.id)
            )
        ).scalars()
    )

    barber_id = uuid.UUID(payload["bid"]) if payload.get("bid") else None
    return AuthContext(
        user=user,
        tenant=tenant,
        role=user.role,
        barber_id=barber_id,
        units=units,
    )


CurrentUser = Annotated[AuthContext, Depends(current_user)]


# --------------------------------------------------------------------------- #
# Authorization
# --------------------------------------------------------------------------- #


def require(permission: Permission) -> Callable[[AuthContext], AuthContext]:
    """
    Require the permission and return the context with the **scope resolved**.

    The endpoint then uses `ctx.scope` to filter:

        if ctx.scope is Scope.OWN:
            q = q.where(Appointment.barber_id == ctx.barber_id)
        elif ctx.scope is Scope.UNIT and not ctx.all_units:
            q = q.where(Appointment.unit_id.in_(ctx.units))
        # tenant_id needs no filter: RLS already took care of it
    """

    def dependency(ctx: CurrentUser) -> AuthContext:
        scope = scope_for(ctx.role, permission)
        if scope is None:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Seu cargo ({ctx.role.value}) não tem a permissão '{permission.value}'",
            )
        if scope is Scope.OWN and ctx.barber_id is None:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Permissão limitada aos próprios registros, mas o usuário não é um barbeiro",
            )
        ctx.scope = scope
        return ctx

    return dependency
