"""The shop's clients. Shared by every unit (spec P3)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.modules.clients.schemas import ClientIn, ClientOut, ClientPage, ClientUpdate
from app.modules.clients.service.create_client import create_client as create_client_action
from app.modules.clients.service.delete_client import delete_client as delete_client_action
from app.modules.clients.service.get_client import get_client as get_client_action
from app.modules.clients.service.list_clients import list_clients as list_clients_action
from app.modules.clients.service.update_client import update_client as update_client_action
from app.modules.identity.public import AuthContext, Permission, SessionDep, require

router = APIRouter(prefix="/clients", tags=["clients"])

ReadClients = Annotated[AuthContext, Depends(require(Permission.CLIENT_READ))]
WriteClients = Annotated[AuthContext, Depends(require(Permission.CLIENT_WRITE))]


@router.get("", response_model=ClientPage, summary="Search clients, one page at a time")
async def list_clients(
    ctx: ReadClients,
    session: SessionDep,
    q: Annotated[str | None, Query(max_length=120, description="Name or phone")] = None,
    active: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """A barber (`own`) sees only the clients they served — none until scheduling exists."""
    return await list_clients_action(session, ctx, q=q, active=active, limit=limit, offset=offset)


@router.post(
    "",
    response_model=ClientOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a client",
)
async def create_client(data: ClientIn, ctx: WriteClients, session: SessionDep):
    """The phone is normalized to E.164 and unique in the shop."""
    return await create_client_action(session, data)


@router.get("/{client_id}", response_model=ClientOut, summary="One client")
async def get_client(client_id: uuid.UUID, ctx: ReadClients, session: SessionDep):
    return await get_client_action(session, ctx, client_id)


@router.patch("/{client_id}", response_model=ClientOut, summary="Update a client")
async def update_client(
    client_id: uuid.UUID, data: ClientUpdate, ctx: WriteClients, session: SessionDep
):
    return await update_client_action(session, ctx, client_id, data)


@router.delete(
    "/{client_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a client without history",
)
async def delete_client(client_id: uuid.UUID, ctx: WriteClients, session: SessionDep):
    """409 when the client has history: inactivate instead (`active: false`)."""
    await delete_client_action(session, ctx, client_id)
