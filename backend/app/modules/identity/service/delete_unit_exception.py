from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.dependencies import AuthContext
from app.modules.identity.service.update_unit_exception import get_configurable_exception


async def delete_unit_exception(
    session: AsyncSession, ctx: AuthContext, exception_id: uuid.UUID
) -> None:
    """Past exceptions may be deleted too (only creating and editing them is refused)."""
    exception, _ = await get_configurable_exception(session, ctx, exception_id)
    await session.delete(exception)
    await session.flush()
