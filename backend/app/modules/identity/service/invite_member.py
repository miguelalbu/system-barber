from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequest, Conflict, Forbidden, NotFound
from app.modules.identity.dependencies import AuthContext
from app.modules.identity.repository import invites as invite_repo
from app.modules.identity.repository import units as unit_repo
from app.modules.identity.repository import users as user_repo
from app.modules.identity.schemas import InviteCreatedOut, InviteIn
from app.modules.identity.service.create_invite import create_invite, invite_link
from app.modules.identity.service.get_barber import get_barber


async def invite_member(
    session: AsyncSession, ctx: AuthContext, data: InviteIn
) -> InviteCreatedOut:
    email = data.email.lower()

    if await user_repo.email_taken(session, email):
        raise Conflict("Já existe um usuário com esse e-mail")

    # Someone who manages only some units cannot grant access to the others.
    if not ctx.all_units:
        outside = set(data.unit_ids) - set(ctx.units)
        if outside or not data.unit_ids:
            raise Forbidden("Você só pode conceder acesso às unidades que administra")

    if data.unit_ids:
        valid = await unit_repo.existing_ids(session, data.unit_ids)
        if valid != set(data.unit_ids):
            raise BadRequest("Unidade inexistente")

    if data.barber_id is not None:
        await _check_barber(session, ctx, data.barber_id)

    record, token = await create_invite(
        session,
        email=email,
        name=data.name,
        role=data.role,
        unit_ids=list(data.unit_ids),
        barber_id=data.barber_id,
        created_by_id=ctx.user.id,
    )

    # Until transactional email exists the link goes back in the response, for
    # the owner to forward over WhatsApp (ISS-004).
    return InviteCreatedOut(invite=record, link=invite_link(ctx.tenant, token))


async def _check_barber(session: AsyncSession, ctx: AuthContext, barber_id: uuid.UUID) -> None:
    """The login will be linked to a registered barber the caller manages, still without access."""
    try:
        barber = await get_barber(session, ctx, barber_id)
    except NotFound as exc:
        raise BadRequest("Barbeiro não encontrado") from exc
    if barber.user_id is not None:
        raise Conflict("Este barbeiro já tem acesso ao painel")
    if await invite_repo.pending_for_barber(session, barber_id, now=datetime.now(UTC)):
        raise Conflict("Já existe um convite pendente para este barbeiro")
