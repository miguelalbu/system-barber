"""`platform_admins` is control plane, in `public` (DEC-003)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.model import PlatformAdmin


async def find_by_email(session: AsyncSession, email: str) -> PlatformAdmin | None:
    return (
        await session.execute(select(PlatformAdmin).where(PlatformAdmin.email == email))
    ).scalar_one_or_none()
