"""
Migrate the control plane, then every shop schema — sequential and fail-fast
(doc Camada 6). Migrations are a deliberate step, never part of booting the
API: `docker compose run --rm migrate`, a CI job, or by hand.

    python -m app.management.migrate                 # list what would run
    python -m app.management.migrate --apply         # control + every tenant
    python -m app.management.migrate --apply --slug central
    python -m app.management.migrate --apply --template   # also tenant_template (checks)

The version recorded in `tenants.schema_version` is what each schema's own
alembic_version says after the run — if a deploy stops halfway, the column
tells the truth.
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from alembic.config import Config
from sqlalchemy import select, text

from alembic import command
from app.core.database import control_session, engine, migrator_engine, quote_identifier
from app.core.schema_version import BACKEND_ROOT, expected_tenant_version
from app.modules.identity.public import Tenant, TenantStatus
from app.modules.provisioning.public import migrate_tenant_schema, read_schema_version

TEMPLATE_SCHEMA = "tenant_template"


def _upgrade_control() -> None:
    config = Config(str(BACKEND_ROOT / "alembic.ini"), ini_section="control")
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic" / "control"))
    config.attributes["configure_logger"] = False
    command.upgrade(config, "head")


async def _schema_exists(schema: str) -> bool:
    async with migrator_engine().connect() as conn:
        found = await conn.scalar(
            text("SELECT 1 FROM pg_namespace WHERE nspname = :name"), {"name": schema}
        )
        return found is not None


async def _targets(slug: str | None) -> list[tuple[str, str, str | None]]:
    async with control_session() as session:
        stmt = select(Tenant).where(Tenant.status != TenantStatus.ARCHIVED).order_by(Tenant.slug)
        if slug:
            stmt = stmt.where(Tenant.slug == slug)
        return [(t.slug, t.schema_name, t.schema_version) for t in (await session.scalars(stmt))]


async def _record(slug: str, version: str | None) -> None:
    async with control_session() as session:
        tenant = await session.scalar(select(Tenant).where(Tenant.slug == slug))
        tenant.schema_version = version


async def _run(args: argparse.Namespace) -> int:
    head = expected_tenant_version()
    if args.apply:
        print("control: upgrading public")
        await asyncio.to_thread(_upgrade_control)

    if args.template:
        print(f"{TEMPLATE_SCHEMA}: {'upgrading' if args.apply else 'would upgrade'}")
        if args.apply:
            async with migrator_engine().begin() as conn:
                q = quote_identifier(TEMPLATE_SCHEMA)
                await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {q}"))
            await migrate_tenant_schema(TEMPLATE_SCHEMA)

    for slug, schema, version in await _targets(args.slug):
        if not await _schema_exists(schema):
            print(f"{slug}: schema {schema} does not exist yet — skipped (provisioning job)")
            continue
        if not args.apply:
            print(f"{slug}: {schema} at {version} → {head}")
            continue
        print(f"{slug}: upgrading {schema}")
        try:
            await _record(slug, await migrate_tenant_schema(schema))
        except Exception as exc:  # noqa: BLE001 — fail fast, but say where
            print(f"{slug}: FAILED — {type(exc).__name__}: {exc}", file=sys.stderr)
            # Record what the schema actually reached before stopping.
            await _record(slug, await read_schema_version(schema))
            return 1

    if not args.apply:
        print("(nothing applied — pass --apply)")
    return 0


async def _main(args: argparse.Namespace) -> int:
    try:
        return await _run(args)
    finally:
        await engine.dispose()
        await migrator_engine().dispose()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.management.migrate")
    parser.add_argument("--apply", action="store_true", help="aplica (sem ele, só lista)")
    parser.add_argument("--slug", help="só esta barbearia")
    parser.add_argument(
        "--template", action="store_true", help=f"inclui {TEMPLATE_SCHEMA} (para alembic check)"
    )
    return asyncio.run(_main(parser.parse_args(argv)))


if __name__ == "__main__":
    raise SystemExit(main())
