from __future__ import annotations

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import Conflict
from app.modules.catalog.repository import services as service_repo
from app.modules.catalog.schemas import ServiceOut, ServiceUpdate
from app.modules.catalog.service._service_out import (
    NAME_TAKEN,
    check_writes_whole_shop,
    service_out,
)
from app.modules.catalog.service.get_service import get_service
from app.modules.identity.public import AuthContext

# Columns that cannot be null: sending `null` for them means "no change".
_REQUIRED = {"name", "duration_minutes", "price_cents", "active"}


async def update_service(
    session: AsyncSession, ctx: AuthContext, service_id: uuid.UUID, data: ServiceUpdate
) -> ServiceOut:
    check_writes_whole_shop(ctx)
    service = await get_service(session, service_id)

    changes = data.model_dump(exclude_unset=True)
    changes = {k: v for k, v in changes.items() if v is not None or k not in _REQUIRED}
    if "name" in changes and await service_repo.name_taken(
        session, changes["name"], exclude_id=service.id
    ):
        raise Conflict(NAME_TAKEN)

    for field, value in changes.items():
        setattr(service, field, value)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise Conflict(NAME_TAKEN) from exc
    return await service_out(session, await get_service(session, service.id))
