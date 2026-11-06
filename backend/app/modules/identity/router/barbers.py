"""
Barbers: the professionals who serve — calendar column, commission, services.

A registry separate from logins (Team): creating a barber never creates a user,
and inviting a user never creates a barber.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.modules.identity.dependencies import AuthContext, SessionDep, require
from app.modules.identity.permissions import Permission
from app.modules.identity.schemas import BarberIn, BarberOut, BarberUpdate
from app.modules.identity.service._barber_rules import barber_out
from app.modules.identity.service.create_barber import create_barber as create_barber_service
from app.modules.identity.service.delete_barber import delete_barber as delete_barber_service
from app.modules.identity.service.get_barber import get_barber as get_barber_service
from app.modules.identity.service.list_barbers import list_barbers as list_barbers_service
from app.modules.identity.service.update_barber import update_barber as update_barber_service

router = APIRouter(prefix="/barbers", tags=["barbers"])

ReadTeam = Annotated[AuthContext, Depends(require(Permission.TEAM_READ))]
ManageTeam = Annotated[AuthContext, Depends(require(Permission.TEAM_MANAGE))]


@router.get("", response_model=list[BarberOut], summary="Barbers in the caller's units")
async def list_barbers(
    ctx: ReadTeam,
    session: SessionDep,
    unit_id: uuid.UUID | None = None,
    active: bool | None = None,
):
    return await list_barbers_service(session, ctx, unit_id=unit_id, active=active)


@router.post(
    "",
    response_model=BarberOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a barber",
)
async def create_barber(data: BarberIn, ctx: ManageTeam, session: SessionDep):
    """Does not create a login. `user_id` links an existing one (an owner who also cuts)."""
    return await create_barber_service(session, ctx, data)


@router.get("/{barber_id}", response_model=BarberOut, summary="One barber")
async def get_barber(barber_id: uuid.UUID, ctx: ReadTeam, session: SessionDep):
    return barber_out(await get_barber_service(session, ctx, barber_id))


@router.patch("/{barber_id}", response_model=BarberOut, summary="Update a barber")
async def update_barber(
    barber_id: uuid.UUID, data: BarberUpdate, ctx: ManageTeam, session: SessionDep
):
    """Partial update. `user_id: null` unlinks the login — refused for a `barber` login."""
    return await update_barber_service(session, ctx, barber_id, data)


@router.delete(
    "/{barber_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a barber without history",
)
async def delete_barber(barber_id: uuid.UUID, ctx: ManageTeam, session: SessionDep):
    """409 when the barber has a login or history: inactivate instead (`active: false`)."""
    await delete_barber_service(session, ctx, barber_id)
