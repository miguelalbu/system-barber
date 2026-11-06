from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import Forbidden, Unauthorized
from app.core.security import hash_password, needs_rehash, verify_password
from app.modules.identity.model import Tenant
from app.modules.identity.repository import barbers as barber_repo
from app.modules.identity.repository import users as user_repo
from app.modules.identity.schemas import LoginIn, TokensOut
from app.modules.identity.service.issue_tokens import issue_tokens

# A real argon2 hash of a value nobody knows. Checked when the e-mail does not
# exist, so a miss costs the same as a hit and the login form cannot be timed
# to find out who works at this shop (doc §4).
DUMMY_HASH = hash_password("dummy-password-nobody-knows-8f1c2a")


async def login(session: AsyncSession, tenant: Tenant, data: LoginIn) -> TokensOut:
    """Staff login on the shop's own domain; the session only sees that shop."""
    user = await user_repo.find_by_email(session, data.email.lower())

    # Same answer — and roughly the same time — for unknown email and wrong
    # password: we do not reveal which emails exist in this shop.
    if user is None:
        verify_password(data.password, DUMMY_HASH)
        raise Unauthorized("E-mail ou senha inválidos")
    if not verify_password(data.password, user.password_hash):
        raise Unauthorized("E-mail ou senha inválidos")
    if not user.active:
        raise Forbidden("Acesso desativado")

    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(data.password)

    user.last_login_at = datetime.now(UTC)
    barber_id = await barber_repo.id_for_user(session, user.id)
    return await issue_tokens(session, tenant, user, barber_id)
