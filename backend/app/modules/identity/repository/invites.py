from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.model import Invite, Role


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


async def claim(session: AsyncSession, token_hash: str, *, now: datetime) -> Invite | None:
    """
    Mark a valid invite as accepted and return it — atomically.

    The conditional UPDATE is what makes an invite single-use for real: two
    simultaneous accepts race on the same row and only one gets it back
    (doc §6, "o convite é de uso único de verdade").
    """
    stmt = (
        update(Invite)
        .where(Invite.token_hash == token_hash)
        .where(Invite.accepted_at.is_(None))
        .where(Invite.expires_at > now)
        .values(accepted_at=now)
        .returning(Invite)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def expire_pending(session: AsyncSession, *, role: Role, now: datetime) -> int:
    """Expire every pending invite of a role — reissuing the owner's first access."""
    stmt = (
        update(Invite)
        .where(Invite.role == role)
        .where(Invite.accepted_at.is_(None))
        .where(Invite.expires_at > now)
        .values(expires_at=now)
    )
    return (await session.execute(stmt)).rowcount


async def latest_by_role(session: AsyncSession, role: Role) -> Invite | None:
    return (
        await session.execute(
            select(Invite).where(Invite.role == role).order_by(Invite.created_at.desc()).limit(1)
        )
    ).scalar_one_or_none()
