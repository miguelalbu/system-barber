from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequest, Conflict
from app.core.security import hash_password, hash_token
from app.modules.identity.model import Barber, Role, User, UserUnit
from app.modules.identity.repository import invites as invite_repo
from app.modules.identity.repository import units as unit_repo
from app.modules.identity.schemas import AcceptInviteIn, MemberOut

INVALID_INVITE = "Convite inválido, expirado ou já utilizado"


def initials_of(name: str) -> str:
    """Two-letter label for a calendar column: "Diego Martins" → "DM"."""
    parts = [p for p in name.split() if p]
    if not parts:
        return "??"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


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

    barber_id: uuid.UUID | None = None
    if record.create_barber or record.role is Role.BARBER:
        unit_id = unit_ids[0] if unit_ids else await unit_repo.first_id(session)
        barber = Barber(
            unit_id=unit_id,
            user_id=user.id,
            name=user.name,
            initials=initials_of(user.name),
        )
        session.add(barber)
        await session.flush()
        barber_id = barber.id

    return MemberOut.model_validate(user).model_copy(update={"barber_id": barber_id})
