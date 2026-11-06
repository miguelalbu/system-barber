from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import set_tenant
from app.core.exceptions import BadRequest
from app.core.security import hash_password, hash_token
from app.modules.identity.model import Barber, Role, Tenant, User, UserUnit
from app.modules.identity.repository import invites as invite_repo
from app.modules.identity.repository import units as unit_repo
from app.modules.identity.schemas import AcceptInviteIn, MemberOut


def initials_of(name: str) -> str:
    """Two-letter label for a calendar column: "Diego Martins" → "DM"."""
    parts = [p for p in name.split() if p]
    if not parts:
        return "??"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


async def accept_invite(session: AsyncSession, tenant: Tenant, data: AcceptInviteIn) -> MemberOut:
    """
    Create the login from an invite.

    The caller has no login yet, so this runs on a platform session; the tenant
    comes from the domain and is pinned here, so the invite token can only match
    an invite of this shop.
    """
    await set_tenant(session, tenant.id)

    record = await invite_repo.find_by_hash(session, hash_token(data.token))

    if record is None or record.accepted_at is not None:
        raise BadRequest("Convite inválido ou já utilizado")
    if record.expires_at <= datetime.now(UTC):
        raise BadRequest("Convite expirado")

    user = User(
        tenant_id=tenant.id,
        email=record.email,
        password_hash=hash_password(data.password),
        name=record.name,
        role=record.role,
    )
    session.add(user)
    await session.flush()

    unit_ids = list(record.unit_ids or [])
    for unit_id in unit_ids:
        session.add(UserUnit(tenant_id=tenant.id, user_id=user.id, unit_id=unit_id))

    barber_id: uuid.UUID | None = None
    if record.create_barber or record.role is Role.BARBER:
        unit_id = unit_ids[0] if unit_ids else await unit_repo.first_id(session)
        barber = Barber(
            tenant_id=tenant.id,
            unit_id=unit_id,
            user_id=user.id,
            name=user.name,
            initials=initials_of(user.name),
        )
        session.add(barber)
        await session.flush()
        barber_id = barber.id

    record.accepted_at = datetime.now(UTC)
    return MemberOut.model_validate(user).model_copy(update={"barber_id": barber_id})
