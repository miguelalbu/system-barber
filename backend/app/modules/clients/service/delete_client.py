from __future__ import annotations

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import Conflict
from app.modules.clients.service.get_client import get_client
from app.modules.identity.public import AuthContext

HAS_HISTORY = "Este cadastro tem histórico; inative em vez de apagar"


async def delete_client(session: AsyncSession, ctx: AuthContext, client_id: uuid.UUID) -> None:
    """
    A real deletion while the client has no history (spec P1). With history
    (future `ON DELETE RESTRICT` references) the database refuses: 409, and the
    path is to inactivate — or, for LGPD, the anonymization of a later spec.
    """
    client = await get_client(session, ctx, client_id)
    await session.delete(client)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise Conflict(HAS_HISTORY) from exc
