from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.model import RefreshToken


async def find_by_hash(session: AsyncSession, token_hash: str) -> RefreshToken | None:
    return (
        await session.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    ).scalar_one_or_none()
