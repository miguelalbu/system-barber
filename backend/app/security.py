"""Password hashing (argon2id), JWTs and opaque invite/refresh tokens."""

from __future__ import annotations

import enum
import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.config import settings

_hasher = PasswordHasher()


# --------------------------------------------------------------------------- #
# Passwords
# --------------------------------------------------------------------------- #


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False
    return True


def needs_rehash(password_hash: str) -> bool:
    """True when the argon2 parameters changed and the hash is worth rewriting."""
    try:
        return _hasher.check_needs_rehash(password_hash)
    except InvalidHashError:
        return False


# --------------------------------------------------------------------------- #
# Opaque tokens (refresh, invite)
# --------------------------------------------------------------------------- #


def generate_opaque_token() -> tuple[str, str]:
    """Returns (plaintext token for the client, sha256 hash for the database)."""
    token = secrets.token_urlsafe(48)
    return token, hash_token(token)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


# --------------------------------------------------------------------------- #
# JWT
# --------------------------------------------------------------------------- #


class TokenType(enum.StrEnum):
    ACCESS = "access"
    SERVICE = "service"  # ai-agent and notification-worker calling the Core API


class InvalidToken(Exception):
    pass


def create_access_token(
    *,
    user_id: uuid.UUID,
    tenant_id: uuid.UUID,
    role: str,
    barber_id: uuid.UUID | None,
) -> tuple[str, int]:
    """
    Short-lived access token.

    Permissions are deliberately **not** in the payload: they are resolved
    server-side from the role. That way a change to the permission map takes
    effect immediately, instead of waiting for every token in circulation to
    expire.
    """
    now = datetime.now(UTC)
    expires = now + timedelta(minutes=settings.access_token_minutes)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "tid": str(tenant_id),
        "rol": role,
        "bid": str(barber_id) if barber_id else None,
        "typ": TokenType.ACCESS.value,
        "jti": secrets.token_urlsafe(12),
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, settings.access_token_minutes * 60


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise InvalidToken("token expirado") from exc
    except jwt.PyJWTError as exc:
        raise InvalidToken("token inválido") from exc


def refresh_expiry() -> datetime:
    return datetime.now(UTC) + timedelta(days=settings.refresh_token_days)


def invite_expiry() -> datetime:
    return datetime.now(UTC) + timedelta(days=settings.invite_expiry_days)
