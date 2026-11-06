from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, generate_opaque_token, refresh_expiry
from app.modules.identity.model import RefreshToken, Tenant, User
from app.modules.identity.schemas import TokensOut


async def issue_tokens(
    session: AsyncSession, tenant: Tenant, user: User, barber_id: uuid.UUID | None
) -> TokensOut:
    """
    A fresh access token plus a rotating refresh token, stored only as a hash
    (DEC-005). The access token names the shop (`tid`); any other host refuses it.
    """
    access, expires_in = create_access_token(
        user_id=user.id,
        tenant_id=tenant.id,
        role=user.role.value,
        barber_id=barber_id,
    )
    refresh, refresh_hash = generate_opaque_token()
    session.add(RefreshToken(user_id=user.id, token_hash=refresh_hash, expires_at=refresh_expiry()))
    return TokensOut(access_token=access, refresh_token=refresh, expires_in=expires_in)
