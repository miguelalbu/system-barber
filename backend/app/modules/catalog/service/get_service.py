from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFound
from app.modules.catalog.model import Service
from app.modules.catalog.repository import services as service_repo


async def get_service(session: AsyncSession, service_id: uuid.UUID) -> Service:
    service = await service_repo.get(session, service_id)
    if service is None:
        raise NotFound("Serviço não encontrado")
    return service
