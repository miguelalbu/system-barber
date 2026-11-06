from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_token
from app.modules.identity.repository import refresh_tokens as refresh_repo


async def logout(session: AsyncSession, refresh_token: str) -> None:
    """Revoke the refresh token. Unknown or already revoked tokens are not an error."""
    record = await refresh_repo.find_by_hash(session, hash_token(refresh_token))
    if record is not None and record.revoked_at is None:
        record.revoked_at = datetime.now(UTC)
