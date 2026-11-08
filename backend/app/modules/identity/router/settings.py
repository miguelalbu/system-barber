"""Public contact and booking policies of the shop (spec S01) — one per shop."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.modules.identity.dependencies import AuthContext, CurrentUser, SessionDep, require
from app.modules.identity.model import ShopSettings
from app.modules.identity.permissions import Permission
from app.modules.identity.schemas import ShopSettingsOut, ShopSettingsUpdate
from app.modules.identity.service.get_shop_settings import get_shop_settings
from app.modules.identity.service.update_shop_settings import update_shop_settings

router = APIRouter(prefix="/tenant", tags=["shop"])

Configure = Annotated[AuthContext, Depends(require(Permission.TENANT_CONFIGURE))]


@router.get("/settings", response_model=ShopSettingsOut, summary="Shop settings")
async def current(_: CurrentUser, session: SessionDep) -> ShopSettings:
    return await get_shop_settings(session)


@router.patch("/settings", response_model=ShopSettingsOut, summary="Update shop settings")
async def update(data: ShopSettingsUpdate, ctx: Configure, session: SessionDep) -> ShopSettings:
    """Partial. Policies apply to the client channels (AI, booking link), not to the staff."""
    return await update_shop_settings(session, ctx, data)
