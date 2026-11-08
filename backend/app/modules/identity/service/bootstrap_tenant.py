from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.model import Role, Tenant, Unit
from app.modules.identity.repository import invites as invite_repo
from app.modules.identity.repository import shop_settings as settings_repo
from app.modules.identity.repository import unit_hours as hours_repo
from app.modules.identity.repository import units as unit_repo
from app.modules.identity.repository import users as user_repo
from app.modules.identity.service._unit_rules import DEFAULT_WEEK
from app.modules.identity.service.create_invite import create_invite, invite_link

DEFAULT_UNIT_NAME = "Unidade principal"


class OwnerAlreadyActive(Exception):
    """The shop already has an owner login; a first-access invite makes no sense."""


async def issue_owner_invite(
    session: AsyncSession, tenant: Tenant, *, owner_name: str, owner_email: str
) -> str:
    """
    The owner's first-access link (single use, `INVITE_EXPIRY_DAYS`). Issuing a
    new one expires the pending ones, so only the latest link works.

    The password never travels in the provisioning contract: the owner sets it
    on the acceptance page (doc §6, "a senha do admin não vai no corpo").
    """
    if await user_repo.find_by_email(session, owner_email.lower()) is not None:
        raise OwnerAlreadyActive(owner_email)
    await invite_repo.expire_pending(session, role=Role.OWNER, now=datetime.now(UTC))
    _, token = await create_invite(
        session,
        email=owner_email,
        name=owner_name,
        role=Role.OWNER,
        unit_ids=[],
        barber_id=None,
        created_by_id=None,
    )
    return invite_link(tenant, token)


async def bootstrap_tenant(
    session: AsyncSession,
    tenant: Tenant,
    *,
    owner_name: str,
    owner_email: str,
    unit_name: str | None,
) -> str | None:
    """
    First data of a new shop: its settings row, its first unit (with the
    default week) and the owner's first-access invite. Idempotent — a retried
    provisioning job does not duplicate the unit, and returns None when the
    owner already exists.
    """
    await settings_repo.get_or_create(session)
    if not await unit_repo.any_exists(session):
        unit = Unit(name=unit_name or DEFAULT_UNIT_NAME)
        session.add(unit)
        await session.flush()
        await hours_repo.replace(session, unit.id, DEFAULT_WEEK)
    try:
        return await issue_owner_invite(
            session, tenant, owner_name=owner_name, owner_email=owner_email
        )
    except OwnerAlreadyActive:
        return None


class NoOwnerInvite(Exception):
    """The shop never had an owner invite (it was not born from provisioning)."""


async def reissue_owner_invite(session: AsyncSession, tenant: Tenant) -> str:
    """
    A new first-access link for the owner the shop was provisioned with — the
    lost-link case (doc §9.3). Reaches only that person: it is not a way to
    create new access. Raises `OwnerAlreadyActive` once they signed up.
    """
    last = await invite_repo.latest_by_role(session, Role.OWNER)
    if last is None:
        raise NoOwnerInvite(tenant.slug)
    return await issue_owner_invite(session, tenant, owner_name=last.name, owner_email=last.email)
