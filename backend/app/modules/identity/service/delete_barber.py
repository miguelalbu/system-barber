from __future__ import annotations

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import Conflict
from app.modules.identity.dependencies import AuthContext
from app.modules.identity.service.get_barber import get_barber

HAS_HISTORY = "Este cadastro tem histórico; inative em vez de apagar"


async def delete_barber(session: AsyncSession, ctx: AuthContext, barber_id: uuid.UUID) -> None:
    """
    Delete for real while nothing points at the barber (spec P1). Records that
    must keep their history (appointments, commissions) reference it with
    `ON DELETE RESTRICT`, so the database refuses and this becomes a 409.
    """
    barber = await get_barber(session, ctx, barber_id)
    if barber.user_id is not None:
        raise Conflict(
            "Este barbeiro tem acesso ao painel; desfaça o vínculo ou desative o acesso "
            "em Equipe antes"
        )
    await session.delete(barber)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise Conflict(HAS_HISTORY) from exc
