"""
Imports every model so `Base.metadata` is complete.

Alembic autogenerate compares the database against this metadata: a model left
out of here looks like a table to drop. Every new module adds its `model`
package below. This is the only file in `core` allowed to import modules
(DEC-008).
"""

from app.core.model_base import Base
from app.modules.identity import model as identity_models  # noqa: F401

__all__ = ["Base"]
