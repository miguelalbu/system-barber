from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.dependencies import AuthContext
from app.modules.identity.model import ShopSettings
from app.modules.identity.repository import shop_settings as settings_repo
from app.modules.identity.schemas import ShopSettingsUpdate

# Contact fields may be cleared with `null`; for a policy `null` means no change.
_NULLABLE = {"contact_phone", "instagram", "about"}


async def update_shop_settings(
    session: AsyncSession, ctx: AuthContext, data: ShopSettingsUpdate
) -> ShopSettings:
    row = await settings_repo.get_or_create(session)
    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        if value is not None or field in _NULLABLE:
            setattr(row, field, value)
    row.updated_by_user_id = ctx.user.id
    await session.flush()
    return await settings_repo.get_or_create(session)
