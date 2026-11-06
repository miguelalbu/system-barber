from __future__ import annotations

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import Conflict
from app.modules.catalog.service._service_out import check_writes_whole_shop
from app.modules.catalog.service.get_service import get_service
from app.modules.identity.public import AuthContext

HAS_HISTORY = "Este cadastro tem histórico; inative em vez de apagar"


async def delete_service(session: AsyncSession, ctx: AuthContext, service_id: uuid.UUID) -> None:
    """
    Delete for real while nothing with history points at it (spec P1); the
    barber links go with it (cascade). Future history (appointments) uses
    `ON DELETE RESTRICT`, so the database refuses and this becomes a 409.
    """
    check_writes_whole_shop(ctx)
    service = await get_service(session, service_id)
    await session.delete(service)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise Conflict(HAS_HISTORY) from exc
