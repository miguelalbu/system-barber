from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.model import ShopSettings
from app.modules.identity.repository import shop_settings as settings_repo


async def get_shop_settings(session: AsyncSession) -> ShopSettings:
    """Contact and booking policies of the shop. Never 404: the row always exists."""
    return await settings_repo.get_or_create(session)
