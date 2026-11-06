"""Shop team: list members, invite, accept an invite, deactivate."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.modules.identity.dependencies import AuthContext, SessionDep, TenantDep, require
from app.modules.identity.permissions import Permission
from app.modules.identity.schemas import (
    AcceptInviteIn,
    InviteCreatedOut,
    InviteIn,
    InviteLookupIn,
    InviteLookupOut,
    InviteOut,
    MemberOut,
)
from app.modules.identity.service.accept_invite import accept_invite as accept_invite_service
from app.modules.identity.service.deactivate_member import deactivate_member
from app.modules.identity.service.invite_member import invite_member
from app.modules.identity.service.list_invites import list_invites as list_invites_service
from app.modules.identity.service.list_members import list_members as list_members_service
from app.modules.identity.service.lookup_invite import lookup_invite

router = APIRouter(prefix="/team", tags=["team"])

ReadTeam = Annotated[AuthContext, Depends(require(Permission.TEAM_READ))]
ManageTeam = Annotated[AuthContext, Depends(require(Permission.TEAM_MANAGE))]


@router.get("", response_model=list[MemberOut], summary="Shop members")
async def list_members(ctx: ReadTeam, session: SessionDep):
    return await list_members_service(session, ctx)


@router.post(
    "/invites",
    response_model=InviteCreatedOut,
    status_code=status.HTTP_201_CREATED,
    summary="Invite someone to the team",
)
async def invite(data: InviteIn, ctx: ManageTeam, session: SessionDep):
    return await invite_member(session, ctx, data)


@router.get("/invites", response_model=list[InviteOut], summary="Pending invites")
async def list_invites(ctx: ReadTeam, session: SessionDep):
    return await list_invites_service(session)


@router.post(
    "/invites/accept",
    status_code=status.HTTP_201_CREATED,
    response_model=MemberOut,
    summary="Accept an invite and create the login",
)
async def accept_invite(data: AcceptInviteIn, tenant: TenantDep, session: SessionDep):
    """
    Public route — the caller has no login yet. The tenant comes from the
    domain, and the invite token has to belong to it. Also the owner's first
    access after provisioning.
    """
    return await accept_invite_service(session, data)


@router.post(
    "/invites/lookup",
    response_model=InviteLookupOut,
    summary="Describe a valid invite without using it",
)
async def lookup(data: InviteLookupIn, tenant: TenantDep, session: SessionDep):
    """
    Public route, for the acceptance page to check the link before asking for
    a password. The token goes in the body, never in a URL that ends up in logs.
    """
    return await lookup_invite(session, data.token)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate a member's access",
)
async def deactivate(user_id: uuid.UUID, ctx: ManageTeam, session: SessionDep):
    """
    Deactivate rather than delete: the appointment and commission history has to
    keep pointing at a real person.
    """
    await deactivate_member(session, ctx, user_id)
