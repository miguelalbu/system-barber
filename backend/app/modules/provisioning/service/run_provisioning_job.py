"""
The provisioning job (doc §6): brings a shop's schema to life, step by step.

Every step is idempotent, and the job records where it is after each one, so a
retry resumes instead of starting over. On failure the shop goes to `failed`
with the error — and nothing is dropped: an automatic `DROP SCHEMA` on a
transient failure is how a customer's data gets erased by accident.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import UTC, datetime

from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import make_url

from alembic import command
from app.core.config import settings
from app.core.database import (
    assert_safe_schema_name,
    control_session,
    migrator_engine,
    quote_identifier,
    tenant_session,
)
from app.core.schema_version import BACKEND_ROOT
from app.modules.identity.public import TenantStatus, bootstrap_tenant
from app.modules.provisioning.model import JobStatus, JobStep
from app.modules.provisioning.repository import catalog as catalog_repo
from app.modules.provisioning.repository import jobs as job_repo

logger = logging.getLogger(__name__)

STEPS = [JobStep.SCHEMA, JobStep.MIGRATIONS, JobStep.GRANTS, JobStep.BOOTSTRAP, JobStep.ACTIVATE]
DML = "SELECT, INSERT, UPDATE, DELETE"

# Alembic keeps its context in module globals: two migrations in one process at
# the same time would trample each other. Jobs migrate one schema at a time.
_migration_lock = asyncio.Lock()


def app_role() -> str:
    """The runtime role, read from DATABASE_URL — never hard-coded."""
    name = make_url(settings.database_url).username
    if not name:
        raise RuntimeError("DATABASE_URL has no username")
    return name


def _upgrade_tenant_schema(schema: str) -> None:
    config = Config(str(BACKEND_ROOT / "alembic.ini"), ini_section="tenant")
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic" / "tenant"))
    config.attributes["schema"] = schema
    config.attributes["configure_logger"] = False
    command.upgrade(config, "head")


async def migrate_tenant_schema(schema: str) -> str | None:
    """Run the tenant chain on one schema and return the version the database reports."""
    assert_safe_schema_name(schema)
    async with _migration_lock:
        # env.py runs its own event loop; a worker thread gives it one.
        await asyncio.to_thread(_upgrade_tenant_schema, schema)
    return await read_schema_version(schema)


async def read_schema_version(schema: str) -> str | None:
    """What the schema's own alembic_version says — the truth, not what we tried."""
    async with migrator_engine().connect() as conn:
        exists = await conn.scalar(
            text("SELECT to_regclass(:table)"), {"table": f"{schema}.alembic_version"}
        )
        if exists is None:
            return None
        return await conn.scalar(
            text(f"SELECT version_num FROM {quote_identifier(schema)}.alembic_version")
        )


async def _step_schema(schema: str) -> None:
    """The schema, plus the runtime role's privileges on whatever gets created in it."""
    q, app = quote_identifier(schema), app_role()
    async with migrator_engine().begin() as conn:
        await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {q}"))
        await conn.execute(text(f'GRANT USAGE ON SCHEMA {q} TO "{app}"'))
        await conn.execute(
            text(f'ALTER DEFAULT PRIVILEGES IN SCHEMA {q} GRANT {DML} ON TABLES TO "{app}"')
        )


async def _step_grants(schema: str) -> None:
    """
    Runtime DML on the tables that exist (covers schemas whose default
    privileges came later), no access to the migration ledger, and the shop's
    own role (doc Camada 3): NOLOGIN, its schema only, never `public` — for
    scoped out-of-band access (support psql, a customer's pg_dump, BI).
    """
    q, app = quote_identifier(schema), app_role()
    async with migrator_engine().begin() as conn:
        await conn.execute(text(f'GRANT {DML} ON ALL TABLES IN SCHEMA {q} TO "{app}"'))
        await conn.execute(text(f'REVOKE ALL ON {q}.alembic_version FROM "{app}"'))
        await conn.execute(
            text(
                f"DO $$ BEGIN "
                f"IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{schema}') THEN "
                f"CREATE ROLE {q} NOLOGIN; END IF; END $$"
            )
        )
        await conn.execute(text(f"GRANT USAGE ON SCHEMA {q} TO {q}"))
        await conn.execute(text(f"GRANT {DML} ON ALL TABLES IN SCHEMA {q} TO {q}"))
        await conn.execute(text(f"REVOKE ALL ON {q}.alembic_version FROM {q}"))
        await conn.execute(
            text(f"ALTER DEFAULT PRIVILEGES IN SCHEMA {q} GRANT {DML} ON TABLES TO {q}")
        )


async def _set_progress(job_id: uuid.UUID, step: JobStep, message: str) -> None:
    async with control_session() as session:
        job = await job_repo.get(session, job_id)
        job.step = step
        job.log += f"{datetime.now(UTC):%Y-%m-%dT%H:%M:%SZ} {message}\n"


async def run_provisioning_job(job_id: uuid.UUID) -> None:
    async with control_session() as session:
        job = await job_repo.get(session, job_id)
        if job is None or job.status is JobStatus.SUCCEEDED:
            return
        tenant = await catalog_repo.get(session, job.tenant_id)
        job.status = JobStatus.RUNNING
        job.error = None
        start = job.step if job.step in STEPS else JobStep.SCHEMA
        # Owner data travels only inside the job's own request payload.
        owner = dict(job.request or {})
        schema = assert_safe_schema_name(tenant.schema_name)

    try:
        for step in STEPS[STEPS.index(start) :]:
            await _set_progress(job_id, step, f"{step}: started")
            if step is JobStep.SCHEMA:
                await _step_schema(schema)
            elif step is JobStep.MIGRATIONS:
                version = await migrate_tenant_schema(schema)
                await _set_progress(job_id, step, f"migrations: at {version}")
            elif step is JobStep.GRANTS:
                await _step_grants(schema)
            elif step is JobStep.BOOTSTRAP:
                async with tenant_session(schema) as session:
                    link = await bootstrap_tenant(
                        session,
                        tenant,
                        owner_name=owner["owner_name"],
                        owner_email=owner["owner_email"],
                        unit_name=owner.get("unit_name"),
                    )
                if link:
                    async with control_session() as session:
                        (await job_repo.get(session, job_id)).setup_token_once = link
            elif step is JobStep.ACTIVATE:
                version = await read_schema_version(schema)
                async with control_session() as session:
                    tenant_row = await catalog_repo.get(session, tenant.id)
                    tenant_row.status = TenantStatus.ACTIVE
                    tenant_row.schema_version = version
                    job = await job_repo.get(session, job_id)
                    job.status = JobStatus.SUCCEEDED
                    job.step = JobStep.DONE
                    job.finished_at = datetime.now(UTC)
                    job.log += f"{datetime.now(UTC):%Y-%m-%dT%H:%M:%SZ} active at {version}\n"
    except Exception as exc:  # noqa: BLE001 — every failure must land on the job, not vanish
        logger.exception("provisioning job %s failed (tenant schema %s)", job_id, schema)
        async with control_session() as session:
            job = await job_repo.get(session, job_id)
            job.status = JobStatus.FAILED
            job.error = f"{type(exc).__name__}: {exc}"[:2000]
            job.finished_at = datetime.now(UTC)
            tenant_row = await catalog_repo.get(session, tenant.id)
            if tenant_row.status is not TenantStatus.ACTIVE:
                tenant_row.status = TenantStatus.FAILED
