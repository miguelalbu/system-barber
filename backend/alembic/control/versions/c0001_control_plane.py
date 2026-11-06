"""Control plane in public: tenant catalog, platform admins, Core keys, jobs, audit

Revision ID: c0001
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "navalha_app"

# What the runtime role may do on each control table — and nothing else.
# No DDL anywhere (DEC-012). Core keys are created by the CLI with the
# migrator credential; the API only reads them and stamps last use.
APP_GRANTS = {
    "tenants": "SELECT, INSERT, UPDATE",
    "platform_admins": "SELECT, INSERT, UPDATE",
    "core_keys": "SELECT, UPDATE",
    "provisioning_jobs": "SELECT, INSERT, UPDATE",
    "core_audit_log": "SELECT, INSERT",
}


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    ]


def upgrade() -> None:
    tenant_status = postgresql.ENUM(
        "provisioning",
        "active",
        "failed",
        "suspended",
        "archived",
        name="tenant_status",
        schema="public",
        create_type=False,
    )
    job_status = postgresql.ENUM(
        "pending",
        "running",
        "succeeded",
        "failed",
        name="job_status",
        schema="public",
        create_type=False,
    )
    job_step = postgresql.ENUM(
        "schema",
        "migrations",
        "grants",
        "bootstrap",
        "activate",
        "done",
        name="job_step",
        schema="public",
        create_type=False,
    )
    for enum_type in (tenant_status, job_status, job_step):
        enum_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(40), nullable=False, unique=True),
        sa.Column("schema_name", sa.String(63), nullable=False, unique=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("custom_domain", sa.String(255), unique=True),
        sa.Column("plan", sa.String(40), nullable=False, server_default="basic"),
        sa.Column("status", tenant_status, nullable=False, server_default="provisioning"),
        sa.Column("schema_version", sa.String(32)),
        sa.Column("external_tenant_id", sa.String(120), unique=True),
        *_timestamps(),
        schema="public",
    )

    op.create_table(
        "platform_admins",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        *_timestamps(),
        schema="public",
    )

    op.create_table(
        "core_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("key_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("scopes", postgresql.ARRAY(sa.String(40)), nullable=False, server_default="{}"),
        sa.Column(
            "ip_allowlist", postgresql.ARRAY(sa.String(64)), nullable=False, server_default="{}"
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        schema="public",
    )

    op.create_table(
        "provisioning_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("public.tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("idempotency_key", sa.String(120), unique=True),
        sa.Column("status", job_status, nullable=False, server_default="pending"),
        sa.Column("step", job_step, nullable=False, server_default="schema"),
        sa.Column("request", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("log", sa.Text, nullable=False, server_default=""),
        sa.Column("error", sa.Text),
        sa.Column("setup_token_once", sa.String(255)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        *_timestamps(),
        schema="public",
    )

    op.create_table(
        "core_audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("core_key_id", postgresql.UUID(as_uuid=True)),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("target", sa.String(120)),
        sa.Column("payload", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("result", sa.String(40), nullable=False),
        sa.Column("ip", sa.String(64)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        schema="public",
    )
    op.create_index("ix_core_audit_created", "core_audit_log", ["created_at"], schema="public")

    harden_public()


def harden_public() -> None:
    """
    `public` is the control plane: nobody gets in by default (doc Camada 3).

    PUBLIC loses every privilege on the schema, so a per-tenant role never
    reaches the catalog. The runtime role gets USAGE plus the DML listed in
    APP_GRANTS. The DO block keeps this harmless where the role has another
    name or is managed by the provider (it is created by infra/postgres/init).
    """
    grants = "\n".join(
        f"GRANT {privileges} ON public.{table} TO {APP_ROLE};"
        for table, privileges in APP_GRANTS.items()
    )
    op.execute("REVOKE ALL ON SCHEMA public FROM PUBLIC")
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{APP_ROLE}') THEN
                GRANT USAGE ON SCHEMA public TO {APP_ROLE};
                {grants}
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    for table in ("core_audit_log", "provisioning_jobs", "core_keys", "platform_admins", "tenants"):
        op.drop_table(table, schema="public")
    for name in ("job_step", "job_status", "tenant_status"):
        op.execute(f"DROP TYPE IF EXISTS public.{name}")
