from __future__ import annotations

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import Conflict
from app.modules.clients.repository import clients as client_repo
from app.modules.clients.schemas import ClientOut, ClientUpdate
from app.modules.clients.service.create_client import PHONE_TAKEN
from app.modules.clients.service.get_client import get_client
from app.modules.identity.public import AuthContext

# Columns that cannot be null: sending `null` for them means "no change".
_REQUIRED = {"name", "phone", "active"}


async def update_client(
    session: AsyncSession, ctx: AuthContext, client_id: uuid.UUID, data: ClientUpdate
) -> ClientOut:
    client = await get_client(session, ctx, client_id)

    changes = data.model_dump(exclude_unset=True)
    changes = {k: v for k, v in changes.items() if v is not None or k not in _REQUIRED}
    if "phone" in changes and await client_repo.phone_taken(
        session, changes["phone"], exclude_id=client.id
    ):
        raise Conflict(PHONE_TAKEN)

    for field, value in changes.items():
        setattr(client, field, value)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise Conflict(PHONE_TAKEN) from exc
    return ClientOut.model_validate(await get_client(session, ctx, client.id))
