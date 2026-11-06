"""
Credentials of the platform Core for the control plane (`X-Core-Key`).

    python -m app.management.core_key create --name core-prod --scopes tenant:read,tenant:provision
    python -m app.management.core_key list
    python -m app.management.core_key revoke <id>

The first key cannot be created over HTTP — nothing could authenticate that
call — so it is created here, with database access: the one credential that
makes sense to demand for minting the most powerful credential in the system.
Runs as the schema owner (DATABASE_URL_MIGRATIONS); the API itself can only
read keys. The raw value is printed once and never stored.
"""

from __future__ import annotations

import argparse
import asyncio
import secrets
import sys
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import migrator_engine
from app.core.security import hash_token
from app.modules.provisioning.public import CoreKey, CoreScope

KEY_PREFIX = "nvc_"  # recognisable in a leaked log or a secret scanner


async def _create(session: AsyncSession, name: str, scopes: list[str], ips: list[str]) -> str:
    valid = {s.value for s in CoreScope}
    unknown = set(scopes) - valid
    if unknown:
        raise SystemExit(f"escopos desconhecidos: {sorted(unknown)} (válidos: {sorted(valid)})")
    raw = KEY_PREFIX + secrets.token_urlsafe(32)
    session.add(CoreKey(name=name, key_hash=hash_token(raw), scopes=scopes, ip_allowlist=ips))
    return raw


async def _run(args: argparse.Namespace) -> int:
    async with AsyncSession(migrator_engine(), expire_on_commit=False) as session:
        async with session.begin():
            if args.command == "create":
                scopes = [s.strip() for s in args.scopes.split(",") if s.strip()]
                ips = [i.strip() for i in (args.ip or "").split(",") if i.strip()]
                raw = await _create(session, args.name, scopes, ips)
                print(f"✓ chave '{args.name}' criada — escopos: {', '.join(scopes)}")
                print("\n  Valor (não será exibido de novo):\n")
                print(f"      {raw}\n")
            elif args.command == "list":
                for key in await session.scalars(select(CoreKey).order_by(CoreKey.created_at)):
                    state = f"revogada {key.revoked_at:%Y-%m-%d}" if key.revoked_at else "ativa"
                    print(f"{key.id}  {key.name:<20} {','.join(key.scopes):<45} {state}")
            elif args.command == "revoke":
                key = await session.get(CoreKey, uuid.UUID(args.id))
                if key is None:
                    print("chave não encontrada", file=sys.stderr)
                    return 1
                key.revoked_at = key.revoked_at or datetime.now(UTC)
                print(f"✓ chave '{key.name}' revogada")
    await migrator_engine().dispose()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.management.core_key")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create", help="cria uma chave e mostra o valor uma vez")
    create.add_argument("--name", required=True)
    create.add_argument("--scopes", required=True, help="ex.: tenant:read,tenant:provision")
    create.add_argument("--ip", help="allowlist opcional, separada por vírgula")
    sub.add_parser("list", help="lista as chaves (sem valores)")
    revoke = sub.add_parser("revoke", help="revoga uma chave")
    revoke.add_argument("id")
    return asyncio.run(_run(parser.parse_args(argv)))


if __name__ == "__main__":
    raise SystemExit(main())
