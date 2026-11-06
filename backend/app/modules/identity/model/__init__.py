"""
Identity and tenancy tables, one file per aggregate.

Importing this package registers every table on `Base.metadata`; that is what
`app/core/model_registry.py` relies on.
"""

from app.modules.identity.model.barber import Barber
from app.modules.identity.model.enums import Role, TenantStatus
from app.modules.identity.model.invite import Invite
from app.modules.identity.model.platform_admin import PlatformAdmin
from app.modules.identity.model.refresh_token import RefreshToken
from app.modules.identity.model.tenant import Tenant
from app.modules.identity.model.unit import Unit
from app.modules.identity.model.user import User, UserUnit

__all__ = [
    "Barber",
    "Invite",
    "PlatformAdmin",
    "RefreshToken",
    "Role",
    "Tenant",
    "TenantStatus",
    "Unit",
    "User",
    "UserUnit",
]
