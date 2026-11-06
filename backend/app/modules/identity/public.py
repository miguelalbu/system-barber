"""
The only surface other modules (and `app/management`) may import from identity.

Typical use in another module's router:

    from app.modules.identity.public import Permission, Scope, SessionDep, require

    ReadAgenda = Annotated[AuthContext, Depends(require(Permission.APPOINTMENT_READ))]
"""

from app.modules.identity.dependencies import (
    AuthContext,
    CurrentUser,
    PlatformSessionDep,
    SessionDep,
    TenantDep,
    require,
)
from app.modules.identity.model.enums import Role, TenantStatus
from app.modules.identity.permissions import Permission, Scope
from app.modules.identity.service.seed_platform_admin import (
    DEFAULT_NAME as DEFAULT_PLATFORM_ADMIN_NAME,
)
from app.modules.identity.service.seed_platform_admin import SeedError, seed_platform_admin

__all__ = [
    "DEFAULT_PLATFORM_ADMIN_NAME",
    "AuthContext",
    "CurrentUser",
    "Permission",
    "PlatformSessionDep",
    "Role",
    "Scope",
    "SeedError",
    "SessionDep",
    "TenantDep",
    "TenantStatus",
    "require",
    "seed_platform_admin",
]
