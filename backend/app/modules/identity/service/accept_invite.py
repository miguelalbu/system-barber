from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequest, Conflict
from app.core.security import hash_password, hash_token
from app.modules.identity.model import Barber, Invite, Role, User, UserUnit
from app.modules.identity.repository import invites as invite_repo
from app.modules.identity.schemas import AcceptInviteIn, MemberOut

INVALID_INVITE = "Convite inválido, expirado ou já utilizado"


async def accept_invite(session: AsyncSession, data: AcceptInviteIn) -> MemberOut:
    """
    Create the login from an invite — a team invite or the owner's first access.

    The session only sees the shop of the domain, so a token can only match an
    invite of that shop. Claiming the invite is a single conditional UPDATE: of
    two simultaneous accepts, one gets the row and the other a 400. If creating
    the user fails afterwards, the claim rolls back with it.
    """
    record = await invite_repo.claim(session, hash_token(data.token), now=datetime.now(UTC))
    if record is None:
        raise BadRequest(INVALID_INVITE)

    user = User(
        email=record.email,
        password_hash=hash_password(data.password),
        name=record.name,
        role=record.role,
    )
    session.add(user)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise Conflict("Já existe um usuário com esse e-mail") from exc

    unit_ids = list(record.unit_ids or [])
    for unit_id in unit_ids:
        session.add(UserUnit(user_id=user.id, unit_id=unit_id))

    barber_id = await _link_barber(session, record, user)
    return MemberOut.model_validate(user).model_copy(update={"barber_id": barber_id})


async def _link_barber(session: AsyncSession, record: Invite, user: User) -> uuid.UUID | None:
    """
    Link the new login to the barber chosen when inviting. Accepting never
    creates a barber — that registry is separate (spec registry-basic-crud).
    """
    barber = await session.get(Barber, record.barber_id) if record.barber_id else None
    if barber is None:
        if record.role is Role.BARBER:
            # The barber was deleted after the invite was sent.
            raise BadRequest("O barbeiro deste convite não existe mais; peça um novo convite")
        return None
    if barber.user_id is not None:
        raise Conflict("Este barbeiro já tem acesso ao painel")
    barber.user_id = user.id
    await session.flush()
    return barber.id
