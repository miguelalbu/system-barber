"""btree_gist: exclusion constraints mixing equality and ranges (unit exceptions, agenda)

Revision ID: c0002
Revises: c0001

Spec: docs/specs/⏳active_identity-units-hours.md. The extension lives in `public`
(created by the migrator, never by the runtime role, DEC-012); shop schemas use
its default operator classes in `EXCLUDE USING gist (unit_id WITH =, … WITH &&)`.
`btree_gist` is a trusted extension, so the database owner may create it.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "c0002"
down_revision: str | None = "c0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist WITH SCHEMA public")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS btree_gist")
