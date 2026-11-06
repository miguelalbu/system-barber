from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BadRequest, Conflict, Forbidden
from app.core.security import generate_opaque_token, invite_expiry
from app.modules.identity.dependencies import AuthContext
from app.modules.identity.model import Invite
from app.modules.identity.repository import units as unit_repo
from app.modules.identity.repository import users as user_repo
from app.modules.identity.schemas import InviteCreatedOut, InviteIn


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

    # Until transactional email exists the link goes back in the response, for
    # the owner to forward over WhatsApp (ISS-004).
    base = f"https://{ctx.tenant.slug}.{settings.base_domain}"
    return InviteCreatedOut(invite=record, link=f"{base}/convite/{token}")
