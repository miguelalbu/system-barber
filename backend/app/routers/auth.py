"""Shop signup, login, rotating refresh, logout and /me."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import set_tenant
from app.deps import CurrentUser, PlatformSessionDep, SessionDep, TenantDep
from app.models import (
    Barber,
    RefreshToken,
    Role,
    Tenant,
    TenantStatus,
    Unit,
    User,
)
from app.permissions import permissions_for
from app.schemas import (
    LoginIn,
    MeOut,
    RefreshIn,
    RegisterShop,
    RegistrationOut,
    TokensOut,
)
from app.security import (
    create_access_token,
    generate_opaque_token,
    hash_password,
    hash_token,
    needs_rehash,
    refresh_expiry,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


async def _issue_tokens(
    session: AsyncSession, user: User, barber_id: uuid.UUID | None
) -> TokensOut:
    access, expires_in = create_access_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
        role=user.role.value,
        barber_id=barber_id,
    )
    refresh, refresh_hash = generate_opaque_token()
    session.add(
        RefreshToken(
            tenant_id=user.tenant_id,
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=refresh_expiry(),
        )
    )
    return TokensOut(access_token=access, refresh_token=refresh, expires_in=expires_in)


async def _barber_id_for(session: AsyncSession, user: User) -> uuid.UUID | None:
    return (
        await session.execute(select(Barber.id).where(Barber.user_id == user.id))
    ).scalar_one_or_none()


@router.post(
    "/register-shop",
    response_model=RegistrationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Provision a new shop with its first owner",
)
async def register_shop(data: RegisterShop, session: PlatformSessionDep):
    if not settings.allow_self_signup:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Auto-cadastro desativado — as barbearias são provisionadas pela equipe",
        )

    tenant = Tenant(
        slug=data.slug,
        name=data.shop_name,
        status=TenantStatus.TRIAL,
        plan="basic",
    )
    session.add(tenant)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Esse endereço já está em uso") from exc

    # From here on the tables have RLS, including on INSERT (WITH CHECK).
    # Without pinning the tenant we just created, the inserts below are refused.
    await set_tenant(session, tenant.id)

    unit = Unit(tenant_id=tenant.id, name=data.unit_name)
    owner = User(
        tenant_id=tenant.id,
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        name=data.owner_name,
        role=Role.OWNER,
    )
    session.add_all([unit, owner])
    await session.flush()

    # The owner gets no unit link: an empty list means "all of them".
    tokens = await _issue_tokens(session, owner, barber_id=None)

    return RegistrationOut(
        tenant=tenant,
        user=owner,
        tokens=tokens,
        panel_url=f"https://{tenant.slug}.{settings.base_domain}",
    )


@router.post("/login", response_model=TokensOut, summary="Staff login")
async def login(data: LoginIn, tenant: TenantDep, session: SessionDep):
    user = (
        await session.execute(select(User).where(User.email == data.email.lower()))
    ).scalar_one_or_none()

    # Same answer for unknown email and wrong password — we do not reveal which
    # emails exist in this shop.
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-mail ou senha inválidos")
    if not user.active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Acesso desativado")

    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(data.password)

    user.last_login_at = datetime.now(UTC)
    barber_id = await _barber_id_for(session, user)
    return await _issue_tokens(session, user, barber_id)


@router.post("/refresh", response_model=TokensOut, summary="Renew the access token")
async def refresh(data: RefreshIn, tenant: TenantDep, session: SessionDep):
    now = datetime.now(UTC)
    record = (
        await session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == hash_token(data.refresh_token))
        )
    ).scalar_one_or_none()

    if record is None or record.revoked_at is not None or record.expires_at <= now:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token inválido ou expirado")

    user = await session.get(User, record.user_id)
    if user is None or not user.active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuário inativo")

    # Rotation: the token just used dies here. If it shows up again, that is a
    # leak signal — reuse detection lands together with auditing.
    record.revoked_at = now
    barber_id = await _barber_id_for(session, user)
    return await _issue_tokens(session, user, barber_id)


@router.post(
    "/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Revoke the refresh token"
)
async def logout(data: RefreshIn, tenant: TenantDep, session: SessionDep):
    record = (
        await session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == hash_token(data.refresh_token))
        )
    ).scalar_one_or_none()
    if record is not None and record.revoked_at is None:
        record.revoked_at = datetime.now(UTC)


@router.get("/me", response_model=MeOut, summary="Current user, shop and permissions")
async def me(ctx: CurrentUser, session: SessionDep):
    stmt = select(Unit).where(Unit.active.is_(True))
    if not ctx.all_units:
        stmt = stmt.where(Unit.id.in_(ctx.units))
    units = list((await session.execute(stmt.order_by(Unit.name))).scalars())

    return MeOut(
        user=ctx.user,
        tenant=ctx.tenant,
        barber_id=ctx.barber_id,
        units=units,
        all_units=ctx.all_units,
        permissions=permissions_for(ctx.role),
    )
