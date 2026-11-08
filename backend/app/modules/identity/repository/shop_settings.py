from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.model import ShopSettings


async def get_or_create(session: AsyncSession) -> ShopSettings:
    """The single row. The migration creates it; this covers a schema created before that."""
    row = await session.get(ShopSettings, 1, populate_existing=True)
    if row is None:
        row = ShopSettings(id=1)
        session.add(row)
        await session.flush()
        await session.refresh(row)
    return row
