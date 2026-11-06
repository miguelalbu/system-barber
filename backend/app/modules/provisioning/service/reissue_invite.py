from __future__ import annotations

import uuid

from app.core.database import control_session, tenant_session
from app.core.exceptions import Conflict
from app.modules.identity.public import (
    NoOwnerInvite,
    OwnerAlreadyActive,
    TenantStatus,
    reissue_owner_invite,
)
from app.modules.provisioning.dependencies import CoreCaller
from app.modules.provisioning.repository import audit as audit_repo
from app.modules.provisioning.schemas import InviteLinkOut
from app.modules.provisioning.service._lookup import tenant_or_404


async def reissue_invite(caller: CoreCaller, tenant_id: uuid.UUID) -> InviteLinkOut:
    """
    A new first-access link for the provisioned owner, invalidating the old
    ones — for when the Core lost the link or the owner let it expire.
    """
    async with control_session() as session:
        tenant = await tenant_or_404(session, tenant_id)
        if tenant.status is not TenantStatus.ACTIVE:
            raise Conflict("A barbearia não está ativa")

    try:
        async with tenant_session(tenant.schema_name) as session:
            link = await reissue_owner_invite(session, tenant)
    except OwnerAlreadyActive as exc:
        raise Conflict("O dono já ativou o acesso — use a recuperação de senha") from exc
    except NoOwnerInvite as exc:
        raise Conflict("Esta barbearia não tem convite de dono para reemitir") from exc

    async with control_session() as session:
        audit_repo.record(
            session,
            core_key_id=caller.key_id,
            action=caller.action,
            target=tenant.slug,
            result="invite_reissued",
            ip=caller.ip,
        )
    return InviteLinkOut(invite_link=link)
