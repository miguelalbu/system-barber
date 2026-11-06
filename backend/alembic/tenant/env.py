"""
Migrations of a shop's schema — the same chain applied to every `tenant_<slug>`.

    alembic -n tenant -x schema=tenant_central upgrade head
    python -m app.management.migrate --apply          (every tenant, in order)

The migration connection uses `SET search_path` to the shop's schema, which is
the Alembic recipe for schema-per-tenant. That is safe **here** and only here:
the connection is private (NullPool) and dies with the run. Request sessions
never touch search_path — they qualify every table (app/core/database.py).
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import MetaData, text
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.database import assert_safe_schema_name, quote_identifier
from app.core.model_registry import TenantBase

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url_migrations)

if config.config_file_name is not None and config.attributes.get("configure_logger", True):
    fileConfig(config.config_file_name)

# The models live under the placeholder schema `tenant`; here the migration
# connection's search_path is the shop's schema, so compare against a copy of
# the metadata with no schema at all.
target_metadata = MetaData()
for _table in TenantBase.metadata.sorted_tables:
    _table.to_metadata(target_metadata, schema=None)

schema = config.attributes.get("schema") or context.get_x_argument(as_dictionary=True).get("schema")
if not schema:
    raise SystemExit("tenant migrations need a schema: -x schema=tenant_<slug>")
assert_safe_schema_name(schema)


def do_run_migrations(connection) -> None:
    quoted = quote_identifier(schema)
    connection.execute(text(f"SET search_path TO {quoted}"))
    connection.commit()
    # Autogenerate compares the metadata (schema None) with the "default"
    # schema; point it at the shop's schema instead of public.
    connection.dialect.default_schema_name = schema

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_schemas=False,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    raise SystemExit("offline mode is not supported for tenant migrations")
asyncio.run(run_migrations_online())
