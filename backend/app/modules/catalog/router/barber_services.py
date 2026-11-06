"""Which services each barber performs."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.modules.catalog.schemas import BarberServicesIn, ServiceOut
from app.modules.catalog.service.set_barber_services import set_barber_services
from app.modules.identity.public import AuthContext, Permission, SessionDep, require

router = APIRouter(prefix="/barbers", tags=["catalog"])

ManageTeam = Annotated[AuthContext, Depends(require(Permission.TEAM_MANAGE))]


@router.put(
    "/{barber_id}/services",
    response_model=list[ServiceOut],
    summary="Set the services a barber performs",
)
async def put_barber_services(
    barber_id: uuid.UUID, data: BarberServicesIn, ctx: ManageTeam, session: SessionDep
):
    """Replaces the whole set (empty list = none). Returns the services now enabled."""
    return await set_barber_services(session, ctx, barber_id, data.service_ids)
