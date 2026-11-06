from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.provisioning.model import CoreAuditLog


def record(
    session: AsyncSession,
    *,
    core_key_id: uuid.UUID | None,
    action: str,
    result: str,
    target: str | None = None,
    payload: dict[str, Any] | None = None,
    ip: str | None = None,
) -> None:
    session.add(
        CoreAuditLog(
            core_key_id=core_key_id,
            action=action,
            target=target,
            payload=payload or {},
            result=result,
            ip=ip,
        )
    )
