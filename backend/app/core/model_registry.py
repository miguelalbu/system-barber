"""
Imports every model so both metadatas are complete.

Alembic autogenerate compares the database against these: a model left out of
here looks like a table to drop. Every new module adds its `model` package
below. This is the only file in `core` allowed to import modules (DEC-008).
"""

from app.core.model_base import ControlBase, TenantBase
from app.modules.catalog import model as catalog_models  # noqa: F401
from app.modules.clients import model as clients_models  # noqa: F401
from app.modules.identity import model as identity_models  # noqa: F401
from app.modules.provisioning import model as provisioning_models  # noqa: F401

__all__ = ["ControlBase", "TenantBase"]
