from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.repository import services as service_repo
from app.modules.catalog.schemas import ServiceOut
from app.modules.catalog.service._service_out import services_out


async def list_services(session: AsyncSession, *, active: bool | None = None) -> list[ServiceOut]:
    """Every service of the shop, by name. Services are shop-wide: no unit scope."""
    return await services_out(session, await service_repo.list_all(session, active=active))
