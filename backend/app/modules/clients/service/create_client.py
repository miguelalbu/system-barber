from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import Conflict
from app.modules.clients.model import Client
from app.modules.clients.repository import clients as client_repo
from app.modules.clients.schemas import ClientIn, ClientOut

PHONE_TAKEN = "Já existe um cliente com esse telefone"


async def create_client(session: AsyncSession, data: ClientIn) -> ClientOut:
    """
    Register a client. Also the entry point for the WhatsApp channel (through
    `public`): the unique E.164 phone is what keeps it from creating duplicates.
    """
    if await client_repo.phone_taken(session, data.phone):
        raise Conflict(PHONE_TAKEN)
    client = Client(**data.model_dump())
    session.add(client)
    try:
        await session.flush()
    except IntegrityError as exc:  # same phone created concurrently
        raise Conflict(PHONE_TAKEN) from exc
    return ClientOut.model_validate(client)
