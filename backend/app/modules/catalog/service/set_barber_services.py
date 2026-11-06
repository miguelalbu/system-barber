from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequest
from app.modules.catalog.repository import barber_services as link_repo
from app.modules.catalog.repository import services as service_repo
from app.modules.catalog.schemas import ServiceOut
from app.modules.catalog.service._service_out import services_out
from app.modules.identity.public import AuthContext, get_barber


async def set_barber_services(
    session: AsyncSession, ctx: AuthContext, barber_id: uuid.UUID, service_ids: list[uuid.UUID]
) -> list[ServiceOut]:
    """Replace the services a barber performs; returns them. Inactive services may stay linked."""
    barber = await get_barber(session, ctx, barber_id)  # 404 outside the caller's units

    wanted = set(service_ids)
    if wanted - await service_repo.existing_ids(session, wanted):
        raise BadRequest("Serviço não encontrado")

    await link_repo.replace_for_barber(session, barber.id, wanted)
    return await services_out(session, await service_repo.list_all(session, ids=wanted))
