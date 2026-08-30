"""Identity core, tenancy and RLS

Revision ID: 0001
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


# Tables holding shop data, which therefore get an RLS policy.
# Every new domain table joins this list in its own migration.
RLS_TABLES = (
    "units",
    "users",
    "user_units",
    "barbers",
    "refresh_tokens",
    "invites",
)

APP_ROLE = "navalha_app"


def apply_rls(table: str) -> None:
    """
    Turn on row-level isolation.

    `ENABLE` alone is not enough: the table owner ignores RLS by default, and
    applications often connect as exactly that. `FORCE` closes that hole.

    Note this does **not** cover superusers, who bypass RLS unconditionally —
    which is why the app connects as `navalha_app` (see infra/postgres/init).

    `NULLIF(..., '')` handles "no tenant pinned": the expression becomes NULL,
    the comparison becomes NULL, and no row passes. Seeing nothing is the safe
    default.
    """
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"""
        CREATE POLICY tenant_isolation ON {table}
            USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
            WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
        """
    )


def grant_privileges() -> None:
    """
    Give the runtime role access to the tables — and nothing more.

    The role itself is created outside the migration (infra/postgres/init)
    because roles belong to the cluster, not the database. The DO block keeps
    this migration harmless in environments where the role has another name or
    is managed by the provider.

    `ALTER DEFAULT PRIVILEGES` makes tables from future migrations accessible on
    creation, so we do not have to repeat GRANT in each one.
    """
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{APP_ROLE}') THEN
                GRANT USAGE ON SCHEMA public TO {APP_ROLE};
                GRANT SELECT, INSERT, UPDATE, DELETE
                    ON ALL TABLES IN SCHEMA public TO {APP_ROLE};
                GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {APP_ROLE};
                ALTER DEFAULT PRIVILEGES IN SCHEMA public
                    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {APP_ROLE};
                ALTER DEFAULT PRIVILEGES IN SCHEMA public
                    GRANT USAGE, SELECT ON SEQUENCES TO {APP_ROLE};
            END IF;
        END
        $$;
        """
    )


def upgrade() -> None:
    # create_type=False: the types are created explicitly right below. Without
    # it, the first create_table referencing an enum would try to create it
    # again and the migration would fail with DuplicateObject.
    tenant_status = postgresql.ENUM(
        "trial", "active", "suspended", "canceled", name="tenant_status", create_type=False
    )
    role = postgresql.ENUM(
        "owner", "manager", "receptionist", "barber", name="role", create_type=False
    )
    tenant_status.create(op.get_bind(), checkfirst=True)
    role.create(op.get_bind(), checkfirst=True)

    # ----------------------------------------------------------------- #
    # Control plane — no tenant_id, no RLS
    # ----------------------------------------------------------------- #

    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(63), nullable=False, unique=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("custom_domain", sa.String(255), unique=True),
        sa.Column("plan", sa.String(40), nullable=False, server_default="basic"),
        sa.Column("status", tenant_status, nullable=False, server_default="trial"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "platform_admins",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    # ----------------------------------------------------------------- #
    # Tenant data
    # ----------------------------------------------------------------- #

    op.create_table(
        "units",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False, server_default="America/Sao_Paulo"),
        sa.Column("address", sa.Text),
        sa.Column("phone", sa.String(32)),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_units_tenant_id", "units", ["tenant_id"])

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("role", role, nullable=False),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("tenant_id", "email", name="uq_user_tenant_email"),
    )
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])
    op.create_index("ix_user_tenant_active", "users", ["tenant_id", "active"])

    op.create_table(
        "user_units",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "unit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("units.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "unit_id", name="uq_user_unit"),
    )
    op.create_index("ix_user_units_tenant_id", "user_units", ["tenant_id"])

    op.create_table(
        "barbers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "unit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("units.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("initials", sa.String(4), nullable=False),
        sa.Column("default_commission", sa.Numeric(5, 2), nullable=False, server_default="40"),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("user_id", name="uq_barber_user"),
    )
    op.create_index("ix_barbers_tenant_id", "barbers", ["tenant_id"])
    op.create_index("ix_barber_tenant_unit", "barbers", ["tenant_id", "unit_id"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_refresh_tokens_tenant_id", "refresh_tokens", ["tenant_id"])
    op.create_index("ix_refresh_user_active", "refresh_tokens", ["user_id", "revoked_at"])

    op.create_table(
        "invites",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("role", role, nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True)),
        sa.Column(
            "unit_ids",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("create_barber", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_invites_tenant_id", "invites", ["tenant_id"])
    op.create_index("ix_invite_tenant_email", "invites", ["tenant_id", "email"])

    for table in RLS_TABLES:
        apply_rls(table)

    grant_privileges()


def downgrade() -> None:
    for table in reversed(RLS_TABLES):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    op.drop_table("invites")
    op.drop_table("refresh_tokens")
    op.drop_table("barbers")
    op.drop_table("user_units")
    op.drop_table("users")
    op.drop_table("units")
    op.drop_table("platform_admins")
    op.drop_table("tenants")

    op.execute("DROP TYPE IF EXISTS role")
    op.execute("DROP TYPE IF EXISTS tenant_status")
