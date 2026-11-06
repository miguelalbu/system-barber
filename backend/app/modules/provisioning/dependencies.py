"""
Authentication of the control plane: the `X-Core-Key` credential (doc §6).

A credential of its own, separate from every shop login: whoever holds a shop
token must never be able to create or destroy shops.
"""

from __future__ import annotations

import hmac
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Header, Request

from app.core.database import control_session
from app.core.exceptions import AppError, Forbidden, Unauthorized
from app.core.rate_limit import RateLimiter
from app.core.security import hash_token
from app.modules.provisioning.model import CoreScope
from app.modules.provisioning.repository import audit as audit_repo
from app.modules.provisioning.repository import core_keys as key_repo

# The Core polls a job every few seconds while a shop provisions, so reads get
# a wide allowance; mutations stay tight (doc §6, "um defeito que o teste revelou").
READ_LIMIT = RateLimiter(limit=240)
WRITE_LIMIT = RateLimiter(limit=20)

# Missing, unknown and revoked keys get the same answer: telling them apart
# would say whether a key ever existed.
INVALID_KEY = "Chave do core inválida"


@dataclass(frozen=True)
class CoreCaller:
    key_id: uuid.UUID
    key_name: str
    ip: str | None
    action: str


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


async def _deny(action: str, ip: str | None, key_id: uuid.UUID | None, exc: AppError) -> AppError:
    """Record the refused call in its own transaction — the request will not commit."""
    async with control_session() as session:
        audit_repo.record(
            session, core_key_id=key_id, action=action, result=f"denied:{exc.status_code}", ip=ip
        )
    return exc


def core_caller(scope: CoreScope, *, write: bool) -> Callable[..., Awaitable[CoreCaller]]:
    async def dependency(
        request: Request,
        x_core_key: Annotated[str | None, Header()] = None,
    ) -> CoreCaller:
        action = f"{request.method} {request.url.path}"
        ip = _client_ip(request)

        if not x_core_key:
            raise await _deny(action, ip, None, Unauthorized(INVALID_KEY))

        presented = hash_token(x_core_key)
        async with control_session() as session:
            key = await key_repo.find_by_hash(session, presented)
            valid = (
                key is not None
                and key.revoked_at is None
                and hmac.compare_digest(key.key_hash, presented)
            )
            if valid:
                key.last_used_at = datetime.now(UTC)

        if not valid:
            raise await _deny(action, ip, key.id if key else None, Unauthorized(INVALID_KEY))
        if key.ip_allowlist and ip not in key.ip_allowlist:
            raise await _deny(action, ip, key.id, Forbidden("Endereço não autorizado"))
        if scope.value not in key.scopes:
            raise await _deny(action, ip, key.id, Forbidden(f"A chave não tem o escopo '{scope}'"))

        try:
            (WRITE_LIMIT if write else READ_LIMIT).hit(str(key.id))
        except AppError as exc:
            raise await _deny(action, ip, key.id, exc) from exc

        return CoreCaller(key_id=key.id, key_name=key.name, ip=ip, action=action)

    return dependency
