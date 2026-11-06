from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import set_tenant
from app.core.exceptions import Conflict, Forbidden
from app.core.security import hash_password
from app.modules.identity.model import Role, Tenant, TenantStatus, Unit, User
from app.modules.identity.schemas import RegisterShop, RegistrationOut
from app.modules.identity.service.issue_tokens import issue_tokens


async def register_shop(session: AsyncSession, data: RegisterShop) -> RegistrationOut:
    """
    Provision a shop: the tenant, its first unit and the owner's login.

    Runs on a platform session (no tenant yet) and pins the new tenant halfway,
    because every table after `tenants` has RLS — including on INSERT.
    """
    if not settings.allow_self_signup:
        raise Forbidden("Auto-cadastro desativado — as barbearias são provisionadas pela equipe")

    tenant = Tenant(
        slug=data.slug,
        name=data.shop_name,
        status=TenantStatus.TRIAL,
        plan="basic",
    )
    session.add(tenant)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise Conflict("Esse endereço já está em uso") from exc

    # From here on the tables have RLS, including on INSERT (WITH CHECK).
    # Without pinning the tenant we just created, the inserts below are refused.
    await set_tenant(session, tenant.id)

    unit = Unit(tenant_id=tenant.id, name=data.unit_name)
    owner = User(
        tenant_id=tenant.id,
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        name=data.owner_name,
        role=Role.OWNER,
    )
    session.add_all([unit, owner])
    await session.flush()

    # The owner gets no unit link: an empty list means "all of them".
    tokens = await issue_tokens(session, owner, barber_id=None)

    return RegistrationOut(
        tenant=tenant,
        user=owner,
        tokens=tokens,
        panel_url=f"https://{tenant.slug}.{settings.base_domain}",
    )
