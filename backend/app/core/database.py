"""
Database access: one connection pool, sessions scoped to a schema.

Every query on shop tables is **qualified** with the shop's schema by
SQLAlchemy's `schema_translate_map` — `"tenant_central"."users"` in the SQL
itself. Nothing in the request path runs `SET search_path`: with a pooled
connection, a session-level search_path survives the request and the next
shop inherits it (doc, Camada 2). That is the worst possible bug here.

* `tenant_session(schema)` — shop tables qualified with that schema; control
  tables (`public`, explicit in their metadata) stay where they are.
* `control_session()` — control plane only.
* `migrator_engine()` — the schema owner, for DDL during provisioning. The
  runtime role (`DATABASE_URL`) has no DDL at all (DEC-012).
"""

from __future__ import annotations

import re
from collections import OrderedDict
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.model_base import TENANT_SCHEMA_PLACEHOLDER

engine = create_async_engine(settings.database_url, pool_pre_ping=True, echo=False)

SessionFactory = async_sessionmaker(expire_on_commit=False)

# The only shape a tenant schema name may have. Re-checked every time a name
# read from the database is about to qualify SQL or reach DDL: a malicious or
# corrupted `tenants.schema_name` must fail here, not become an identifier.
SAFE_SCHEMA_NAME = re.compile(r"^tenant_[a-z][a-z0-9_]{1,39}$")

_TENANT_BINDS_MAX = 64
_tenant_binds: OrderedDict[str, AsyncEngine] = OrderedDict()


class UnsafeSchemaName(ValueError):
    pass


def assert_safe_schema_name(schema_name: str) -> str:
    if not isinstance(schema_name, str) or not SAFE_SCHEMA_NAME.fullmatch(schema_name):
        raise UnsafeSchemaName(f"unsafe tenant schema name: {schema_name!r}")
    return schema_name


def tenant_bind(schema_name: str) -> AsyncEngine:
    """
    A thin engine over the shared pool that qualifies shop tables with
    `schema_name`. Cached (LRU) — never one pool per tenant, which is how
    `max_connections` runs out.
    """
    assert_safe_schema_name(schema_name)
    bind = _tenant_binds.get(schema_name)
    if bind is None:
        bind = engine.execution_options(
            schema_translate_map={TENANT_SCHEMA_PLACEHOLDER: schema_name}
        )
        _tenant_binds[schema_name] = bind
        if len(_tenant_binds) > _TENANT_BINDS_MAX:
            _tenant_binds.popitem(last=False)
    else:
        _tenant_binds.move_to_end(schema_name)
    return bind


@asynccontextmanager
async def tenant_session(schema_name: str) -> AsyncIterator[AsyncSession]:
    """Session with an open transaction on a shop's schema. Commits on exit."""
    async with SessionFactory(bind=tenant_bind(schema_name)) as session:
        async with session.begin():
            yield session


@asynccontextmanager
async def control_session() -> AsyncIterator[AsyncSession]:
    """
    Session for the control plane tables in `public`. A shop table touched from
    here points at the placeholder schema `tenant`, which does not exist —
    which is the point: it fails instead of reading the wrong place.
    """
    async with SessionFactory(bind=engine) as session:
        async with session.begin():
            yield session


@lru_cache
def migrator_engine() -> AsyncEngine:
    """The schema owner. DDL only (provisioning, destroy); never request data."""
    return create_async_engine(settings.database_url_migrations, poolclass=NullPool)


def quote_identifier(name: str) -> str:
    """A validated schema/role name, quoted by the dialect for use in DDL."""
    assert_safe_schema_name(name)
    return engine.dialect.identifier_preparer.quote_identifier(name)
