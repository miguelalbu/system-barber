"""Services the shop sells. Shop-wide: one price for every unit."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.modules.catalog.schemas import ServiceIn, ServiceOut, ServiceUpdate
from app.modules.catalog.service._service_out import service_out
from app.modules.catalog.service.create_service import create_service as create_service_action
from app.modules.catalog.service.delete_service import delete_service as delete_service_action
from app.modules.catalog.service.get_service import get_service as get_service_action
from app.modules.catalog.service.list_services import list_services as list_services_action
from app.modules.catalog.service.update_service import update_service as update_service_action
from app.modules.identity.public import AuthContext, Permission, SessionDep, require

router = APIRouter(prefix="/services", tags=["catalog"])

ReadCatalog = Annotated[AuthContext, Depends(require(Permission.CATALOG_READ))]
WriteCatalog = Annotated[AuthContext, Depends(require(Permission.CATALOG_WRITE))]


@router.get("", response_model=list[ServiceOut], summary="Services of the shop")
async def list_services(ctx: ReadCatalog, session: SessionDep, active: bool | None = None):
    return await list_services_action(session, active=active)


@router.post(
    "",
    response_model=ServiceOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a service",
)
async def create_service(data: ServiceIn, ctx: WriteCatalog, session: SessionDep):
    """Requires access to every unit: a service is priced for all of them."""
    return await create_service_action(session, ctx, data)


@router.get("/{service_id}", response_model=ServiceOut, summary="One service")
async def get_service(service_id: uuid.UUID, ctx: ReadCatalog, session: SessionDep):
    return await service_out(session, await get_service_action(session, service_id))


@router.patch("/{service_id}", response_model=ServiceOut, summary="Update a service")
async def update_service(
    service_id: uuid.UUID, data: ServiceUpdate, ctx: WriteCatalog, session: SessionDep
):
    return await update_service_action(session, ctx, service_id, data)


@router.delete(
    "/{service_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a service without history",
)
async def delete_service(service_id: uuid.UUID, ctx: WriteCatalog, session: SessionDep):
    """409 when it has history: inactivate instead (`active: false`)."""
    await delete_service_action(session, ctx, service_id)
