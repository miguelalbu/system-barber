from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import generate_opaque_token, invite_expiry
from app.modules.identity.model import Invite, Role, Tenant


def invite_link(tenant: Tenant, token: str) -> str:
    """The acceptance page on the shop's own address — its domain when it has one."""
    host = tenant.custom_domain or f"{tenant.slug}.{settings.base_domain}"
    return f"https://{host}/convite/{token}"


async def create_invite(
    session: AsyncSession,
    *,
    email: str,
    name: str,
    role: Role,
    unit_ids: list[uuid.UUID],
    create_barber: bool,
    created_by_id: uuid.UUID | None,
) -> tuple[Invite, str]:
    """Store an invite (only the token's hash) and return it with the raw token."""
    token, token_hash = generate_opaque_token()
    record = Invite(
        email=email.lower(),
        name=name,
        role=role,
        token_hash=token_hash,
        expires_at=invite_expiry(),
        created_by_id=created_by_id,
        unit_ids=list(unit_ids),
        create_barber=create_barber,
    )
    session.add(record)
    await session.flush()
    return record, token
