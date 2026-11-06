"""
Which tenant schema version this build expects (doc Camada 6).

Read from the tenant migration folder that ships inside the image, so there is
no number for anyone to remember to bump: code and schema cannot drift apart
by forgetfulness.

Only **behind** is refused. A schema ahead of the code is safe by construction
(migrations are expand/contract) and is exactly what happens mid rolling
deploy, while some instances still run the previous build. A version never
recorded (None) is not treated as behind either.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

BACKEND_ROOT = Path(__file__).resolve().parents[2]
TENANT_MIGRATIONS = BACKEND_ROOT / "alembic" / "tenant"


@lru_cache
def _script() -> ScriptDirectory:
    config = Config()
    config.set_main_option("script_location", str(TENANT_MIGRATIONS))
    return ScriptDirectory.from_config(config)


@lru_cache
def expected_tenant_version() -> str:
    head = _script().get_current_head()
    if head is None:
        raise RuntimeError("tenant migration chain has no head")
    return head


@lru_cache
def _older_than_head() -> frozenset[str]:
    head = expected_tenant_version()
    return frozenset(rev.revision for rev in _script().walk_revisions() if rev.revision != head)


def is_behind(version: str | None) -> bool:
    """True when `version` is a known ancestor of this build's head."""
    return version is not None and version in _older_than_head()
