"""Barber working time: weekly schedule, special shifts, time off and blocks

Revision ID: t0004
Revises: t0003

Spec: docs/specs/⏳active_scheduling-barber-schedule.md. Expand only (new
tables). The time-off overlap constraint uses `btree_gist` (control c0002).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "t0004"
down_revision: str | None = "t0003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

KINDS = ("day_off", "vacation", "sick_leave", "block")


def _barber_fk() -> sa.Column:
    return sa.Column(
        "barber_id",
        postgresql.UUID(as_uuid=True),
        sa.ForeignKey("barbers.id", ondelete="CASCADE"),
        nullable=False,
    )


def _created_by() -> sa.Column:
    return sa.Column(
        "created_by_user_id",
        postgresql.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
    )


def _now(name: str) -> sa.Column:
    return sa.Column(name, sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)


def upgrade() -> None:
    op.create_table(
        "barber_work_hours",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        _barber_fk(),
        sa.Column("weekday", sa.SmallInteger, nullable=False),
        sa.Column("starts_at", sa.Time, nullable=False),
        sa.Column("ends_at", sa.Time, nullable=False),
        sa.CheckConstraint("weekday BETWEEN 1 AND 7", name="ck_barber_hours_weekday"),
        sa.CheckConstraint("starts_at < ends_at", name="ck_barber_hours_interval"),
    )
    op.create_index("ix_barber_hours_barber_weekday", "barber_work_hours", ["barber_id", "weekday"])

    op.create_table(
        "barber_shift_overrides",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        _barber_fk(),
        sa.Column("on_date", sa.Date, nullable=False),
        sa.Column("starts_at", sa.Time, nullable=False),
        sa.Column("ends_at", sa.Time, nullable=False),
        sa.Column("reason", sa.String(120)),
        _created_by(),
        _now("created_at"),
        sa.CheckConstraint("starts_at < ends_at", name="ck_shift_override_interval"),
    )
    op.create_index(
        "ix_shift_override_barber_date", "barber_shift_overrides", ["barber_id", "on_date"]
    )

    postgresql.ENUM(*KINDS, name="time_off_kind").create(op.get_bind())
    op.create_table(
        "barber_time_off",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        _barber_fk(),
        sa.Column(
            "kind", postgresql.ENUM(*KINDS, name="time_off_kind", create_type=False), nullable=False
        ),
        sa.Column("all_day", sa.Boolean, nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.String(200)),
        _created_by(),
        _now("created_at"),
        _now("updated_at"),
        sa.CheckConstraint("ends_at > starts_at", name="ck_time_off_range"),
        postgresql.ExcludeConstraint(
            ("barber_id", "="),
            (sa.text("tstzrange(starts_at, ends_at, '[)')"), "&&"),
            name="ex_time_off_overlap",
            using="gist",
        ),
    )


def downgrade() -> None:
    op.drop_table("barber_time_off")
    postgresql.ENUM(name="time_off_kind").drop(op.get_bind())
    op.drop_table("barber_shift_overrides")
    op.drop_table("barber_work_hours")
