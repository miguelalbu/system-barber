from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import Conflict
from app.modules.catalog.model import Service
from app.modules.catalog.repository import services as service_repo
from app.modules.catalog.schemas import ServiceIn, ServiceOut
from app.modules.catalog.service._service_out import (
    NAME_TAKEN,
    check_writes_whole_shop,
    service_out,
)
from app.modules.identity.public import AuthContext


async def create_service(session: AsyncSession, ctx: AuthContext, data: ServiceIn) -> ServiceOut:
    check_writes_whole_shop(ctx)
    if await service_repo.name_taken(session, data.name):
        raise Conflict(NAME_TAKEN)

    service = Service(**data.model_dump())
    session.add(service)
    try:
        await session.flush()
    except IntegrityError as exc:  # same name created concurrently
        raise Conflict(NAME_TAKEN) from exc
    return await service_out(session, service)
