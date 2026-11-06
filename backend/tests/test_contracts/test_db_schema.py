"""The ORM schema as Alembic sees it — control plane and shop schema, separately."""

from __future__ import annotations

from sqlalchemy import Enum

from app.core.model_registry import ControlBase, TenantBase
from tests.test_contracts._snapshot import assert_matches_snapshot


def _column(col) -> dict:
    data = {
        "type": str(col.type),
        "nullable": col.nullable,
        "primary_key": col.primary_key,
        "unique": bool(col.unique),
        "index": bool(col.index),
        "server_default": str(col.server_default.arg) if col.server_default is not None else None,
        "foreign_keys": sorted(
            f"{fk.target_fullname} ondelete={fk.ondelete}" for fk in col.foreign_keys
        ),
    }
    if isinstance(col.type, Enum):
        data["enum"] = {
            "name": col.type.name,
            "schema": col.type.schema,
            "values": list(col.type.enums),
        }
    return data


def _schema(metadata) -> dict:
    return {
        name: {
            "columns": {col.name: _column(col) for col in table.columns},
            "indexes": sorted(
                f"{ix.name}({', '.join(c.name for c in ix.columns)})"
                + (" unique" if ix.unique else "")
                for ix in table.indexes
            ),
            "constraints": sorted(
                f"{type(c).__name__}:{c.name}({', '.join(col.name for col in c.columns)})"
                for c in table.constraints
                if c.name
            ),
        }
        for name, table in sorted(metadata.tables.items())
    }


def test_orm_schema_is_stable():
    assert_matches_snapshot(
        "db_schema",
        {
            "control (public)": _schema(ControlBase.metadata),
            "tenant (per shop)": _schema(TenantBase.metadata),
        },
    )
