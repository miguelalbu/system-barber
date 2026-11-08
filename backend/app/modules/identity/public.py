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
from app.modules.identity.service.barber_views import BarberInfo, list_barber_infos
from app.modules.identity.service.barber_views import barber_info as get_barber_info
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
from app.modules.identity.service.unit_calendar import (
    ShopPolicies,
    UnitCalendar,
    UnitInfo,
)
from app.modules.identity.service.unit_calendar import list_unit_infos as list_units
from app.modules.identity.service.unit_calendar import shop_policies as get_shop_settings
from app.modules.identity.service.unit_calendar import unit_calendar as get_unit_calendar
from app.modules.identity.service.unit_calendar import unit_info as get_unit
from app.modules.identity.service.unit_calendar import unit_week as get_unit_week
from app.modules.identity.tenant_naming import InvalidSlug, schema_name_for, validate_slug

__all__ = [
    "DEFAULT_PLATFORM_ADMIN_NAME",
    "AuthContext",
    "BarberInfo",
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
    "ShopPolicies",
    "Tenant",
    "TenantDep",
    "TenantStatus",
    "UnitCalendar",
    "UnitInfo",
    "bootstrap_tenant",
    "get_barber",
    "get_barber_info",
    "get_shop_settings",
    "get_unit",
    "get_unit_calendar",
    "get_unit_week",
    "issue_owner_invite",
    "list_barber_infos",
    "list_units",
    "reissue_owner_invite",
    "require",
    "schema_name_for",
    "seed_platform_admin",
    "validate_slug",
]
