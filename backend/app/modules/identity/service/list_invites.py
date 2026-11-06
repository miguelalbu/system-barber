from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.model import Invite
from app.modules.identity.repository import invites as invite_repo


async def list_invites(session: AsyncSession) -> list[Invite]:
    """Invites neither accepted nor expired, newest first."""
    return await invite_repo.list_pending(session, now=datetime.now(UTC))
