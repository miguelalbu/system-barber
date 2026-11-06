from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.provisioning.model import CoreKey


async def find_by_hash(session: AsyncSession, key_hash: str) -> CoreKey | None:
    return (
        await session.execute(select(CoreKey).where(CoreKey.key_hash == key_hash))
    ).scalar_one_or_none()
