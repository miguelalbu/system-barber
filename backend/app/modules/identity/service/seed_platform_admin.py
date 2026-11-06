"""
Create or update the platform admin (DEC-003).

A platform admin is *our* staff, not a shop's: the account exists outside every
tenant and outside the tenant RBAC, for cross-tenant support. Its table is the
only identity outside every shop schema — so treat the credentials accordingly.

Unlike the request-scoped services, this one owns its transaction: it is
driven by the operator CLI (`app/management/seed.py`), not by a route.
"""

from __future__ import annotations

import secrets
from typing import Literal

from pydantic import EmailStr, TypeAdapter, ValidationError

from app.core.database import control_session
from app.core.exceptions import BadRequest
from app.core.security import hash_password
from app.modules.identity.model import PlatformAdmin
from app.modules.identity.repository import platform_admins as admin_repo

# Stricter than the 8 characters required of a shop user: this account reaches
# across every tenant, so it is the single most valuable credential we hold.
MIN_PASSWORD_LENGTH = 12

DEFAULT_NAME = "Suporte Navalha"

SeedAction = Literal["created", "updated", "unchanged"]

_email_validator = TypeAdapter(EmailStr)


class SeedError(BadRequest):
    """Something the operator has to fix — reported without a traceback."""


def _generate_password() -> str:
    return secrets.token_urlsafe(18)


def _normalize_email(value: str) -> str:
    try:
        return str(_email_validator.validate_python(value.strip())).lower()
    except ValidationError as exc:
        raise SeedError(f"E-mail inválido: {value!r}") from exc


async def seed_platform_admin(
    *,
    email: str,
    name: str | None = None,
    password: str | None = None,
    update_password: bool = False,
) -> tuple[SeedAction, str | None]:
    """
    `name` is optional on purpose: when updating an existing account, leaving it
    out keeps the name already stored, so resetting a password does not quietly
    rename the person.

    Returns the action taken and the generated password when we produced one, so
    the caller can display it — the only time it is ever readable.
    """
    email = _normalize_email(email)
    name = name.strip() if name else None
    if name == "":
        raise SeedError("O nome não pode ficar em branco")

    generated: str | None = None
    if password is None:
        generated = _generate_password()
        password = generated
    elif len(password) < MIN_PASSWORD_LENGTH:
        raise SeedError(
            f"A senha precisa de pelo menos {MIN_PASSWORD_LENGTH} caracteres "
            f"(recebeu {len(password)})"
        )

    async with control_session() as session:
        existing = await admin_repo.find_by_email(session, email)

        if existing is not None:
            if not update_password:
                # Idempotent by default: re-running the seed on a provisioned
                # environment must never silently rotate a live credential.
                return "unchanged", None
            existing.password_hash = hash_password(password)
            if name:
                existing.name = name
            # Resetting the password of a disabled account is how access is
            # restored, so re-enable it.
            existing.active = True
            return "updated", generated

        session.add(
            PlatformAdmin(
                email=email,
                password_hash=hash_password(password),
                name=name or DEFAULT_NAME,
            )
        )
        return "created", generated
