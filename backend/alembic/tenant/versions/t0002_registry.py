"""Basic registry: services, barber ↔ service links, clients; invites point at a barber

Revision ID: t0002
Revises: t0001

Spec: docs/specs/✅completed_registry-basic-crud.md. Expand only — new tables and
one new nullable column — so the previous build keeps working on shops not yet
migrated. `invites.create_barber` stops being read but is dropped only in a
later (contract) migration. No GRANT: the schema's default privileges, set by
provisioning, already cover new tables (DEC-012).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "t0002"
down_revision: str | None = "t0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


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
    op.create_table(
        "services",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("description", sa.String(500)),
        sa.Column("duration_minutes", sa.SmallInteger, nullable=False),
        sa.Column("price_cents", sa.Integer, nullable=False),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        *_timestamps(),
        sa.CheckConstraint(
            "duration_minutes BETWEEN 5 AND 480 AND duration_minutes % 5 = 0",
            name="ck_service_duration",
        ),
        sa.CheckConstraint("price_cents >= 0", name="ck_service_price"),
    )
    op.create_index("uq_service_name", "services", [sa.text("lower(name)")], unique=True)

    op.create_table(
        "barber_services",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "barber_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("barbers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "service_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("services.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.UniqueConstraint("barber_id", "service_id", name="uq_barber_service"),
    )
    op.create_index("ix_barber_service_service", "barber_services", ["service_id"])

    op.create_table(
        "clients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("phone", sa.String(16), nullable=False),
        sa.Column("email", sa.String(255)),
        sa.Column("birth_date", sa.Date),
        sa.Column("notes", sa.String(1000)),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        *_timestamps(),
        sa.UniqueConstraint("phone", name="uq_client_phone"),
    )

    op.add_column(
        "invites",
        sa.Column(
            "barber_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("barbers.id", ondelete="SET NULL"),
        ),
    )


def downgrade() -> None:
    op.drop_column("invites", "barber_id")
    for table in ("clients", "barber_services", "services"):
        op.drop_table(table)
