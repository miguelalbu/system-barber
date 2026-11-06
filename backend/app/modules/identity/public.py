"""
The only surface other modules (and `app/management`) may import from identity.

Typical use in another module's router:

    from app.modules.identity.public import Permission, Scope, SessionDep, require

    ReadAgenda = Annotated[AuthContext, Depends(require(Permission.APPOINTMENT_READ))]
"""

from app.modules.identity.dependencies import (
    AuthContext,
    ControlSessionDep,
    CurrentUser,
    SessionDep,
    TenantDep,
    require,
)
from app.modules.identity.model import Tenant
from app.modules.identity.model.enums import Role, TenantStatus
from app.modules.identity.permissions import Permission, Scope
from app.modules.identity.service.bootstrap_tenant import (
    NoOwnerInvite,
    OwnerAlreadyActive,
    bootstrap_tenant,
    issue_owner_invite,
    reissue_owner_invite,
)
from app.modules.identity.service.get_barber import get_barber
from app.modules.identity.service.seed_platform_admin import (
    DEFAULT_NAME as DEFAULT_PLATFORM_ADMIN_NAME,
)
from app.modules.identity.service.seed_platform_admin import SeedError, seed_platform_admin
from app.modules.identity.tenant_naming import InvalidSlug, schema_name_for, validate_slug

__all__ = [
    "DEFAULT_PLATFORM_ADMIN_NAME",
    "AuthContext",
    "ControlSessionDep",
    "CurrentUser",
    "InvalidSlug",
    "NoOwnerInvite",
    "OwnerAlreadyActive",
    "Permission",
    "Role",
    "Scope",
    "SeedError",
    "SessionDep",
    "Tenant",
    "TenantDep",
    "TenantStatus",
    "bootstrap_tenant",
    "get_barber",
    "issue_owner_invite",
    "reissue_owner_invite",
    "require",
    "schema_name_for",
    "seed_platform_admin",
    "validate_slug",
]
