"""
Migrations of the control plane — the `public` schema (DEC-011).

    alembic -n control upgrade head      (or: python -m app.management.migrate --apply)
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.model_registry import ControlBase

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url_migrations)

# Programmatic runs (the migrate command, provisioning) keep the app's logging.
if config.config_file_name is not None and config.attributes.get("configure_logger", True):
    fileConfig(config.config_file_name)

target_metadata = ControlBase.metadata


def _configure(**kwargs) -> None:
    # include_schemas stays off: only the default schema (public) is compared,
    # so tenant schemas never show up as tables to drop.
    context.configure(target_metadata=target_metadata, compare_type=True, **kwargs)


def run_migrations_offline() -> None:
    _configure(url=settings.database_url_migrations, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    _configure(connection=connection)
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
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
