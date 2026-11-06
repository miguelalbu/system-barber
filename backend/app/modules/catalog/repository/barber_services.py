import uuid
from collections import defaultdict
from collections.abc import Iterable

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.model import BarberService


async def barbers_by_service(
    session: AsyncSession, service_ids: Iterable[uuid.UUID]
) -> dict[uuid.UUID, list[uuid.UUID]]:
    """service_id → barber_ids, for the given services."""
    rows = await session.execute(
        select(BarberService.service_id, BarberService.barber_id).where(
            BarberService.service_id.in_(list(service_ids))
        )
    )
    result: dict[uuid.UUID, list[uuid.UUID]] = defaultdict(list)
    for service_id, barber_id in rows.all():
        result[service_id].append(barber_id)
    return result


async def replace_for_barber(
    session: AsyncSession, barber_id: uuid.UUID, service_ids: set[uuid.UUID]
) -> None:
    await session.execute(delete(BarberService).where(BarberService.barber_id == barber_id))
    session.add_all(BarberService(barber_id=barber_id, service_id=s) for s in service_ids)
    await session.flush()
