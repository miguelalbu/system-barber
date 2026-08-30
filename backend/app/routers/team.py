"""Shop team: list members, invite, accept an invite, deactivate."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.config import settings
from app.db import set_tenant
from app.deps import AuthContext, PlatformSessionDep, SessionDep, TenantDep, require
from app.models import Barber, Invite, Role, Unit, User, UserUnit
from app.permissions import Permission
from app.schemas import (
    AcceptInviteIn,
    InviteCreatedOut,
    InviteIn,
    InviteOut,
    MemberOut,
)
from app.security import generate_opaque_token, hash_password, hash_token, invite_expiry

router = APIRouter(prefix="/team", tags=["team"])

ReadTeam = Annotated[AuthContext, Depends(require(Permission.TEAM_READ))]
ManageTeam = Annotated[AuthContext, Depends(require(Permission.TEAM_MANAGE))]


def _initials(name: str) -> str:
    parts = [p for p in name.split() if p]
    if not parts:
        return "??"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


@router.get("", response_model=list[MemberOut], summary="Shop members")
async def list_members(ctx: ReadTeam, session: SessionDep):
    # RLS already limits us to the tenant; here we only apply the unit scope.
    stmt = select(User).order_by(User.name)
    if not ctx.all_units:
        stmt = stmt.where(
            User.id.in_(select(UserUnit.user_id).where(UserUnit.unit_id.in_(ctx.units)))
        )
    users = list((await session.execute(stmt)).scalars())

    links = dict(
        (
            await session.execute(
                select(Barber.user_id, Barber.id).where(Barber.user_id.is_not(None))
            )
        ).all()
    )

    return [
        MemberOut.model_validate(u).model_copy(update={"barber_id": links.get(u.id)})
        for u in users
    ]


@router.post(
    "/invites",
    response_model=InviteCreatedOut,
    status_code=status.HTTP_201_CREATED,
    summary="Invite someone to the team",
)
async def invite(data: InviteIn, ctx: ManageTeam, session: SessionDep):
    email = data.email.lower()

    exists = (
        await session.execute(select(User.id).where(User.email == email))
    ).scalar_one_or_none()
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe um usuário com esse e-mail")

    # Someone who manages only some units cannot grant access to the others.
    if not ctx.all_units:
        outside = set(data.unit_ids) - set(ctx.units)
        if outside or not data.unit_ids:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Você só pode conceder acesso às unidades que administra",
            )

    if data.unit_ids:
        valid = set(
            (await session.execute(select(Unit.id).where(Unit.id.in_(data.unit_ids)))).scalars()
        )
        if valid != set(data.unit_ids):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unidade inexistente")

    token, token_hash = generate_opaque_token()
    record = Invite(
        tenant_id=ctx.tenant.id,
        email=email,
        name=data.name,
        role=data.role,
        token_hash=token_hash,
        expires_at=invite_expiry(),
        created_by_id=ctx.user.id,
        unit_ids=list(data.unit_ids),
        create_barber=data.create_barber,
    )
    session.add(record)
    await session.flush()

    base = f"https://{ctx.tenant.slug}.{settings.base_domain}"
    return InviteCreatedOut(invite=record, link=f"{base}/convite/{token}")


@router.get("/invites", response_model=list[InviteOut], summary="Pending invites")
async def list_invites(ctx: ReadTeam, session: SessionDep):
    stmt = (
        select(Invite)
        .where(Invite.accepted_at.is_(None))
        .where(Invite.expires_at > datetime.now(UTC))
        .order_by(Invite.created_at.desc())
    )
    return list((await session.execute(stmt)).scalars())


@router.post(
    "/invites/accept",
    status_code=status.HTTP_201_CREATED,
    response_model=MemberOut,
    summary="Accept an invite and create the login",
)
async def accept_invite(data: AcceptInviteIn, tenant: TenantDep, session: PlatformSessionDep):
    """
    Public route — the caller has no login yet. The tenant comes from the
    domain, and the invite token has to belong to it.
    """
    await set_tenant(session, tenant.id)

    record = (
        await session.execute(select(Invite).where(Invite.token_hash == hash_token(data.token)))
    ).scalar_one_or_none()

    if record is None or record.accepted_at is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Convite inválido ou já utilizado")
    if record.expires_at <= datetime.now(UTC):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Convite expirado")

    user = User(
        tenant_id=tenant.id,
        email=record.email,
        password_hash=hash_password(data.password),
        name=record.name,
        role=record.role,
    )
    session.add(user)
    await session.flush()

    unit_ids = list(record.unit_ids or [])
    for unit_id in unit_ids:
        session.add(UserUnit(tenant_id=tenant.id, user_id=user.id, unit_id=unit_id))

    barber_id: uuid.UUID | None = None
    if record.create_barber or record.role is Role.BARBER:
        unit_id = unit_ids[0] if unit_ids else None
        if unit_id is None:
            unit_id = (
                await session.execute(select(Unit.id).order_by(Unit.created_at).limit(1))
            ).scalar_one()
        barber = Barber(
            tenant_id=tenant.id,
            unit_id=unit_id,
            user_id=user.id,
            name=user.name,
            initials=_initials(user.name),
        )
        session.add(barber)
        await session.flush()
        barber_id = barber.id

    record.accepted_at = datetime.now(UTC)
    return MemberOut.model_validate(user).model_copy(update={"barber_id": barber_id})


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate a member's access",
)
async def deactivate(user_id: uuid.UUID, ctx: ManageTeam, session: SessionDep):
    """
    Deactivate rather than delete: the appointment and commission history has to
    keep pointing at a real person.
    """
    if user_id == ctx.user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Você não pode desativar a si mesmo")

    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuário não encontrado")
    if user.role is Role.OWNER:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "O dono não pode ser desativado")

    user.active = False
