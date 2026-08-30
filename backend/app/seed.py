"""
Seed script for the platform admin account.

A platform admin is *our* staff, not a shop's: the account exists outside every
tenant and outside the tenant RBAC, for cross-tenant support. There is exactly
one of these tables that is not isolated by RLS, and this is it — so treat the
credentials accordingly.

    # inside the container
    docker compose exec core-api python -m app.seed platform-admin

    # on the host, with the venv
    ./.venv/Scripts/python.exe -m app.seed platform-admin \
        --email suporte@navalha.app --name "Miguel Albuquerque"

Values fall back to the SEED_ADMIN_EMAIL, SEED_ADMIN_NAME and
SEED_ADMIN_PASSWORD environment variables. With no password given, a strong one
is generated and printed once — that is the only time it is ever readable.

Running twice is safe: an existing account is left untouched unless you pass
--update-password.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import secrets
import sys

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import select

from app.config import settings
from app.db import engine, platform_session
from app.models import PlatformAdmin
from app.security import hash_password

# Stricter than the 8 characters required of a shop user: this account reaches
# across every tenant, so it is the single most valuable credential we hold.
MIN_PASSWORD_LENGTH = 12

_email_validator = TypeAdapter(EmailStr)


class SeedError(Exception):
    """Something the operator has to fix — reported without a traceback."""


def _generate_password() -> str:
    return secrets.token_urlsafe(18)


def _normalize_email(value: str) -> str:
    try:
        return str(_email_validator.validate_python(value.strip())).lower()
    except ValidationError as exc:
        raise SeedError(f"E-mail inválido: {value!r}") from exc


DEFAULT_NAME = "Suporte Navalha"


async def seed_platform_admin(
    *,
    email: str,
    name: str | None = None,
    password: str | None = None,
    update_password: bool = False,
) -> tuple[str, str | None]:
    """
    Create (or update) the platform admin.

    `name` is optional on purpose: when updating an existing account, leaving it
    out keeps the name already stored, so resetting a password does not quietly
    rename the person.

    Returns the action taken — "created", "updated" or "unchanged" — and the
    generated password when we produced one, so the caller can display it.
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

    async with platform_session() as session:
        existing = (
            await session.execute(select(PlatformAdmin).where(PlatformAdmin.email == email))
        ).scalar_one_or_none()

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


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m app.seed",
        description="Popula dados iniciais que não vêm de migration.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    admin = subcommands.add_parser(
        "platform-admin",
        help="cria a conta de suporte da plataforma (cross-tenant)",
    )
    admin.add_argument(
        "--email",
        default=os.getenv("SEED_ADMIN_EMAIL"),
        help="padrão: variável SEED_ADMIN_EMAIL",
    )
    admin.add_argument(
        "--name",
        default=os.getenv("SEED_ADMIN_NAME"),
        help=f"padrão: variável SEED_ADMIN_NAME, ou {DEFAULT_NAME!r} ao criar; "
        "ao atualizar, omitir mantém o nome atual",
    )
    admin.add_argument(
        "--password",
        default=os.getenv("SEED_ADMIN_PASSWORD"),
        help="padrão: variável SEED_ADMIN_PASSWORD; sem nenhuma das duas, "
        "uma senha forte é gerada e exibida uma única vez",
    )
    admin.add_argument(
        "--update-password",
        action="store_true",
        help="redefine a senha se a conta já existir (por padrão, não mexe)",
    )
    return parser.parse_args(argv)


async def _run(args: argparse.Namespace) -> int:
    if not args.email:
        raise SeedError("Informe --email ou defina SEED_ADMIN_EMAIL")

    action, generated = await seed_platform_admin(
        email=args.email,
        name=args.name,
        password=args.password,
        update_password=args.update_password,
    )

    if action == "unchanged":
        print(f"· {args.email} já existe — nada alterado.")
        print("  Use --update-password para redefinir a senha.")
        return 0

    verb = "criada" if action == "created" else "atualizada"
    print(f"✓ Conta de plataforma {verb}: {args.email}")

    if generated:
        print()
        print("  Senha gerada (não será exibida de novo):")
        print(f"      {generated}")
        print()
        if not settings.dev:
            print("  Guarde-a agora, em um gerenciador de senhas.")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    try:
        return asyncio.run(_main(args))
    except SeedError as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 1


async def _main(args: argparse.Namespace) -> int:
    try:
        return await _run(args)
    finally:
        # Without this the process hangs on the open asyncpg pool.
        await engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
