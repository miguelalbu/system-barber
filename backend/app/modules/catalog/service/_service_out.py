"""Response shape shared by the catalog actions."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import Forbidden
from app.modules.catalog.model import Service
from app.modules.catalog.repository import barber_services as link_repo
from app.modules.catalog.schemas import ServiceOut
from app.modules.identity.public import AuthContext

NAME_TAKEN = "Já existe um serviço com esse nome"


def check_writes_whole_shop(ctx: AuthContext) -> None:
    """A service is priced for every unit (spec P4): only who sees them all may change it."""
    if not ctx.all_units:
        raise Forbidden("Serviços valem para todas as unidades; peça a quem administra todas")


async def services_out(session: AsyncSession, services: list[Service]) -> list[ServiceOut]:
    links = await link_repo.barbers_by_service(session, [s.id for s in services])
    return [
        ServiceOut(
            id=s.id,
            name=s.name,
            description=s.description,
            duration_minutes=s.duration_minutes,
            price_cents=s.price_cents,
            active=s.active,
            barber_ids=links.get(s.id, []),
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in services
    ]


async def service_out(session: AsyncSession, service: Service) -> ServiceOut:
    return (await services_out(session, [service]))[0]
