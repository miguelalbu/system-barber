"""
Operator commands that populate data no migration creates.

    # inside the container
    docker compose exec core-api python -m app.management.seed platform-admin

    # on the host, with the venv (or: make seed-admin)
    .venv/bin/python -m app.management.seed platform-admin \
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
import sys

from app.core.config import settings
from app.core.database import engine
from app.modules.identity.public import DEFAULT_PLATFORM_ADMIN_NAME as DEFAULT_NAME
from app.modules.identity.public import SeedError, seed_platform_admin


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m app.management.seed",
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
