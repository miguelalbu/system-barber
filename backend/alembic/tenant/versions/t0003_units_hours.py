"""Units: weekly hours, calendar exceptions, online booking flag; shop settings

Revision ID: t0003
Revises: t0002

Spec: docs/specs/⏳active_identity-units-hours.md. Expand only. Needs the
`btree_gist` extension (control c0002) for the exception overlap constraint.
Data: the single `shop_settings` row and the default weekly hours (Mon–Sat
09:00–19:00) for every unit that exists, so no agenda is born empty (T6).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "t0003"
down_revision: str | None = "t0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

KIND = postgresql.ENUM("closed", "special_hours", name="unit_exception_kind", create_type=False)


def upgrade() -> None:
    op.add_column(
        "units",
        sa.Column("online_booking", sa.Boolean, nullable=False, server_default=sa.true()),
    )
    op.create_index("uq_unit_name", "units", [sa.text("lower(name)")], unique=True)

    op.create_table(
        "unit_business_hours",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "unit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("units.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("weekday", sa.SmallInteger, nullable=False),
        sa.Column("opens_at", sa.Time, nullable=False),
        sa.Column("closes_at", sa.Time, nullable=False),
        sa.CheckConstraint("weekday BETWEEN 1 AND 7", name="ck_unit_hours_weekday"),
        sa.CheckConstraint("opens_at < closes_at", name="ck_unit_hours_interval"),
    )
    op.create_index("ix_unit_hours_unit_weekday", "unit_business_hours", ["unit_id", "weekday"])

    postgresql.ENUM("closed", "special_hours", name="unit_exception_kind").create(op.get_bind())
    op.create_table(
        "unit_exceptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "unit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("units.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("starts_on", sa.Date, nullable=False),
        sa.Column("ends_on", sa.Date, nullable=False),
        sa.Column("kind", KIND, nullable=False),
        sa.Column("opens_at", sa.Time),
        sa.Column("closes_at", sa.Time),
        sa.Column("reason", sa.String(120)),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("ends_on >= starts_on", name="ck_unit_exception_dates"),
        sa.CheckConstraint(
            "(kind = 'closed' AND opens_at IS NULL AND closes_at IS NULL)"
            " OR (kind = 'special_hours' AND opens_at < closes_at)",
            name="ck_unit_exception_hours",
        ),
        postgresql.ExcludeConstraint(
            ("unit_id", "="),
            (sa.text("daterange(starts_on, ends_on, '[]')"), "&&"),
            name="ex_unit_exception_overlap",
            using="gist",
        ),
    )

    op.create_table(
        "shop_settings",
        sa.Column("id", sa.SmallInteger, primary_key=True),
        sa.Column("contact_phone", sa.String(16)),
        sa.Column("instagram", sa.String(60)),
        sa.Column("about", sa.String(1000)),
        sa.Column("min_advance_minutes", sa.SmallInteger, nullable=False, server_default="60"),
        sa.Column("max_advance_days", sa.SmallInteger, nullable=False, server_default="30"),
        sa.Column(
            "confirmation_deadline_hours", sa.SmallInteger, nullable=False, server_default="3"
        ),
        sa.Column("client_change_min_hours", sa.SmallInteger, nullable=False, server_default="2"),
        sa.Column("late_tolerance_minutes", sa.SmallInteger, nullable=False, server_default="10"),
        sa.Column(
            "max_future_appointments_per_client",
            sa.SmallInteger,
            nullable=False,
            server_default="3",
        ),
        sa.Column(
            "barber_sees_client_contact", sa.Boolean, nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "updated_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("id = 1", name="ck_shop_settings_single_row"),
        sa.CheckConstraint(
            "min_advance_minutes BETWEEN 0 AND 2880 AND min_advance_minutes % 15 = 0",
            name="ck_shop_settings_min_advance",
        ),
        sa.CheckConstraint(
            "max_advance_days BETWEEN 1 AND 180", name="ck_shop_settings_max_advance"
        ),
        sa.CheckConstraint(
            "confirmation_deadline_hours BETWEEN 1 AND 48", name="ck_shop_settings_confirmation"
        ),
        sa.CheckConstraint(
            "client_change_min_hours BETWEEN 0 AND 72", name="ck_shop_settings_client_change"
        ),
        sa.CheckConstraint("late_tolerance_minutes BETWEEN 0 AND 60", name="ck_shop_settings_late"),
        sa.CheckConstraint(
            "max_future_appointments_per_client BETWEEN 1 AND 20",
            name="ck_shop_settings_future_limit",
        ),
    )

    op.execute("INSERT INTO shop_settings (id) VALUES (1) ON CONFLICT DO NOTHING")
    # Default hours (T6): Monday to Saturday, 09:00–19:00, for every existing unit.
    op.execute(
        "INSERT INTO unit_business_hours (id, unit_id, weekday, opens_at, closes_at) "
        "SELECT gen_random_uuid(), u.id, d, TIME '09:00', TIME '19:00' "
        "FROM units u CROSS JOIN generate_series(1, 6) AS d"
    )


def downgrade() -> None:
    op.drop_table("shop_settings")
    op.drop_table("unit_exceptions")
    postgresql.ENUM(name="unit_exception_kind").drop(op.get_bind())
    op.drop_table("unit_business_hours")
    op.drop_index("uq_unit_name", table_name="units")
    op.drop_column("units", "online_booking")
