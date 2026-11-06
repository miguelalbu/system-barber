from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequest
from app.core.security import hash_token
from app.modules.identity.repository import invites as invite_repo
from app.modules.identity.schemas import InviteLookupOut
from app.modules.identity.service.accept_invite import INVALID_INVITE


async def lookup_invite(session: AsyncSession, token: str) -> InviteLookupOut:
    """
    Describe a valid invite without spending it, so the screen can say "this
    link expired" before asking for a password twice (doc §6, fechamento).
    """
    record = await invite_repo.find_by_hash(session, hash_token(token))
    if record is None or record.accepted_at is not None or record.expires_at <= datetime.now(UTC):
        raise BadRequest(INVALID_INVITE)
    return InviteLookupOut.model_validate(record)
