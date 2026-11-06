from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import Unauthorized
from app.core.security import hash_token
from app.modules.identity.model import Tenant
from app.modules.identity.repository import barbers as barber_repo
from app.modules.identity.repository import refresh_tokens as refresh_repo
from app.modules.identity.repository import users as user_repo
from app.modules.identity.schemas import TokensOut
from app.modules.identity.service.issue_tokens import issue_tokens


async def refresh_session(session: AsyncSession, tenant: Tenant, refresh_token: str) -> TokensOut:
    now = datetime.now(UTC)
    record = await refresh_repo.find_by_hash(session, hash_token(refresh_token))

    if record is None or record.revoked_at is not None or record.expires_at <= now:
        raise Unauthorized("Refresh token inválido ou expirado")

    user = await user_repo.get(session, record.user_id)
    if user is None or not user.active:
        raise Unauthorized("Usuário inativo")

    # Rotation: the token just used dies here. If it shows up again, that is a
    # leak signal — reuse detection lands together with auditing (ISS-003).
    record.revoked_at = now
    barber_id = await barber_repo.id_for_user(session, user.id)
    return await issue_tokens(session, tenant, user, barber_id)
