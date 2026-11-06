from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import Forbidden, Unauthorized
from app.core.security import hash_password, needs_rehash, verify_password
from app.modules.identity.repository import barbers as barber_repo
from app.modules.identity.repository import users as user_repo
from app.modules.identity.schemas import LoginIn, TokensOut
from app.modules.identity.service.issue_tokens import issue_tokens


async def login(session: AsyncSession, data: LoginIn) -> TokensOut:
    """Staff login. The tenant is already pinned on the session (it came from the domain)."""
    user = await user_repo.find_by_email(session, data.email.lower())

    # Same answer for unknown email and wrong password — we do not reveal which
    # emails exist in this shop.
    if user is None or not verify_password(data.password, user.password_hash):
        raise Unauthorized("E-mail ou senha inválidos")
    if not user.active:
        raise Forbidden("Acesso desativado")

    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(data.password)

    user.last_login_at = datetime.now(UTC)
    barber_id = await barber_repo.id_for_user(session, user.id)
    return await issue_tokens(session, user, barber_id)
