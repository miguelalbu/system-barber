from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnprocessableEntity
from app.modules.identity.public import AuthContext
from app.modules.scheduling.service.update_time_off import reachable_time_off


async def delete_time_off(session: AsyncSession, ctx: AuthContext, time_off_id: uuid.UUID) -> None:
    """
    Past whole days may be deleted (vacation entered by mistake); a past block
    stays — it records why the slot was empty.
    """
    row, _ = await reachable_time_off(session, ctx, time_off_id)
    if not row.kind.all_day and row.ends_at <= datetime.now(UTC):
        raise UnprocessableEntity("Bloqueio passado não pode ser apagado")
    await session.delete(row)
    await session.flush()
