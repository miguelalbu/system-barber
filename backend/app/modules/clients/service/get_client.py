from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFound
from app.modules.clients.model import Client
from app.modules.clients.repository import clients as client_repo
from app.modules.identity.public import AuthContext, Scope


async def get_client(session: AsyncSession, ctx: AuthContext, client_id: uuid.UUID) -> Client:
    # `own` reaches only clients the barber served — none until scheduling exists.
    client = None if ctx.scope is Scope.OWN else await client_repo.get(session, client_id)
    if client is None:
        raise NotFound("Cliente não encontrado")
    return client
