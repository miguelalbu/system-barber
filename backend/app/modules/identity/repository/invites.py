from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.model import Invite


async def find_by_hash(session: AsyncSession, token_hash: str) -> Invite | None:
    return (
        await session.execute(select(Invite).where(Invite.token_hash == token_hash))
    ).scalar_one_or_none()


async def list_pending(session: AsyncSession, *, now: datetime) -> list[Invite]:
    stmt = (
        select(Invite)
        .where(Invite.accepted_at.is_(None))
        .where(Invite.expires_at > now)
        .order_by(Invite.created_at.desc())
    )
    return list((await session.execute(stmt)).scalars())
