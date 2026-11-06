"""
FastAPI dependencies: tenant resolution, database session and authorization.

The chain is always the same, in this order:

    Host → Tenant (control plane) → servable? → session on the shop's schema
         → user from the JWT (same shop) → permission

Other modules reach these through `app.modules.identity.public`.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import control_session, tenant_session
from app.core.exceptions import Forbidden, NotFound, ServiceUnavailable, Unauthorized
from app.core.schema_version import is_behind
from app.core.security import InvalidToken, TokenType, decode_token
from app.modules.identity.model import Role, Tenant, TenantStatus, User
from app.modules.identity.permissions import Permission, Scope, scope_for
from app.modules.identity.repository import tenants as tenant_repo
from app.modules.identity.repository import users as user_repo

# --------------------------------------------------------------------------- #
# Tenant from the domain
# --------------------------------------------------------------------------- #


def _hostname(request: Request) -> str:
    host = request.headers.get("host", "")
    return host.split(":")[0].lower().strip()


def _not_found(host: str) -> NotFound:
    return NotFound(f"Barbearia não encontrada para '{host}'")


def assert_servable(tenant: Tenant, host: str) -> None:
    """
    Only an active shop whose schema is not behind this build is served
    (DEC-013). Archived looks exactly like unknown.
    """
    if tenant.status is TenantStatus.ARCHIVED:
        raise _not_found(host)
    if tenant.status is TenantStatus.SUSPENDED:
        raise Forbidden("Assinatura inativa")
    if tenant.status is not TenantStatus.ACTIVE:
        raise ServiceUnavailable("Barbearia em preparação — tente de novo em instantes")
    if is_behind(tenant.schema_version):
        raise ServiceUnavailable("Barbearia em manutenção — tente de novo em instantes")


async def resolve_tenant(
    request: Request,
    x_tenant_slug: Annotated[str | None, Header()] = None,
) -> Tenant:
    """
    Find the shop from the access domain — its personalized subdomain or its
    own domain (DEC-002):

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

    async with control_session() as session:
        tenant = (
            await tenant_repo.find_by_slug(session, slug)
            if slug
            else await tenant_repo.find_by_custom_domain(session, host)
        )

    if tenant is None:
        raise _not_found(host)
    assert_servable(tenant, host)

    request.state.tenant = tenant
    return tenant


TenantDep = Annotated[Tenant, Depends(resolve_tenant)]


async def get_session(tenant: TenantDep) -> AsyncIterator[AsyncSession]:
    """
    Session whose shop tables are qualified with this shop's schema — read from
    `tenants.schema_name`, never derived from the request (doc Camada 2).
    """
    async with tenant_session(tenant.schema_name) as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_control_session() -> AsyncIterator[AsyncSession]:
    """Control plane tables only (`public`). Shop tables are unreachable from here."""
    async with control_session() as session:
        yield session


ControlSessionDep = Annotated[AsyncSession, Depends(get_control_session)]


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

    @property
    def unit_filter(self) -> list[uuid.UUID] | None:
        """The units to filter by, or None when the user sees the whole shop."""
        return None if self.all_units else self.units

    @property
    def scoped_units(self) -> list[uuid.UUID] | None:
        """`unit_filter` under the resolved scope: an `all` permission ignores linked units."""
        return None if self.scope is Scope.ALL else self.unit_filter

    def reaches_unit(self, unit_id: uuid.UUID) -> bool:
        units = self.scoped_units
        return units is None or unit_id in units


def _bearer(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise Unauthorized("Credenciais ausentes", headers={"WWW-Authenticate": "Bearer"})
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
        raise Unauthorized(str(exc)) from exc

    if payload.get("typ") != TokenType.ACCESS.value:
        raise Unauthorized("Tipo de token incorreto")

    # A token issued for another shop never works here, even though we signed it.
    if payload.get("tid") != str(tenant.id):
        raise Forbidden("Token de outra barbearia")

    user = await user_repo.get(session, uuid.UUID(payload["sub"]))
    if user is None or not user.active:
        raise Unauthorized("Usuário inativo ou inexistente")

    barber_id = uuid.UUID(payload["bid"]) if payload.get("bid") else None
    return AuthContext(
        user=user,
        tenant=tenant,
        role=user.role,
        barber_id=barber_id,
        units=await user_repo.unit_ids_of(session, user.id),
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
        # no tenant filter: the session only sees this shop's schema
    """

    def dependency(ctx: CurrentUser) -> AuthContext:
        scope = scope_for(ctx.role, permission)
        if scope is None:
            raise Forbidden(
                f"Seu cargo ({ctx.role.value}) não tem a permissão '{permission.value}'"
            )
        if scope is Scope.OWN and ctx.barber_id is None:
            raise Forbidden(
                "Permissão limitada aos próprios registros, mas o usuário não é um barbeiro"
            )
        ctx.scope = scope
        return ctx

    return dependency
