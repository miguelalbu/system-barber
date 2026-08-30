"""
Tenant RBAC.

Project rule: **code never asks for the role, it asks for the permission.**

    if ctx.role == Role.OWNER:              # no
    Depends(require(P.FINANCE_READ))        # yes

The role → permission map lives here and nowhere else. When a customer asks
"I want the front desk to see today's revenue", that is one line in this file —
not forty endpoints.
"""

from __future__ import annotations

import enum

from app.models import Role


class Scope(enum.StrEnum):
    """
    How far a permission reaches. RBAC alone cannot express "a barber may read
    appointments, but only their own" — that is what this axis covers.
    """

    ALL = "all"  # the whole shop
    UNIT = "unit"  # only the units linked to the user
    OWN = "own"  # only the barber's own records


class Permission(enum.StrEnum):
    APPOINTMENT_READ = "appointment:read"
    APPOINTMENT_CREATE = "appointment:create"
    APPOINTMENT_UPDATE = "appointment:update"
    APPOINTMENT_CANCEL = "appointment:cancel"

    CLIENT_READ = "client:read"
    CLIENT_WRITE = "client:write"

    CATALOG_READ = "catalog:read"
    CATALOG_WRITE = "catalog:write"

    TICKET_READ = "ticket:read"
    TICKET_WRITE = "ticket:write"
    FINANCE_READ = "finance:read"
    FINANCE_WRITE = "finance:write"
    COMMISSION_READ = "commission:read"

    CONVERSATION_READ = "conversation:read"
    CONVERSATION_REPLY = "conversation:reply"

    TEAM_READ = "team:read"
    TEAM_MANAGE = "team:manage"

    TENANT_CONFIGURE = "tenant:configure"
    SUBSCRIPTION_MANAGE = "subscription:manage"


P = Permission
S = Scope

_EVERYTHING: dict[Permission, Scope] = {p: S.ALL for p in Permission}

_MANAGER: dict[Permission, Scope] = {
    P.APPOINTMENT_READ: S.UNIT,
    P.APPOINTMENT_CREATE: S.UNIT,
    P.APPOINTMENT_UPDATE: S.UNIT,
    P.APPOINTMENT_CANCEL: S.UNIT,
    P.CLIENT_READ: S.UNIT,
    P.CLIENT_WRITE: S.UNIT,
    P.CATALOG_READ: S.UNIT,
    P.CATALOG_WRITE: S.UNIT,
    P.TICKET_READ: S.UNIT,
    P.TICKET_WRITE: S.UNIT,
    P.FINANCE_READ: S.UNIT,
    P.FINANCE_WRITE: S.UNIT,
    P.COMMISSION_READ: S.UNIT,
    P.CONVERSATION_READ: S.UNIT,
    P.CONVERSATION_REPLY: S.UNIT,
    P.TEAM_READ: S.UNIT,
    P.TEAM_MANAGE: S.UNIT,
    # No TENANT_CONFIGURE and no SUBSCRIPTION_MANAGE: those belong to the owner.
}

_RECEPTIONIST: dict[Permission, Scope] = {
    P.APPOINTMENT_READ: S.UNIT,
    P.APPOINTMENT_CREATE: S.UNIT,
    P.APPOINTMENT_UPDATE: S.UNIT,
    P.APPOINTMENT_CANCEL: S.UNIT,
    P.CLIENT_READ: S.UNIT,
    P.CLIENT_WRITE: S.UNIT,
    P.CATALOG_READ: S.UNIT,
    P.TICKET_READ: S.UNIT,
    P.TICKET_WRITE: S.UNIT,
    P.CONVERSATION_READ: S.UNIT,
    P.CONVERSATION_REPLY: S.UNIT,
    P.TEAM_READ: S.UNIT,
    # No finance: the front desk closes tickets, it does not see revenue.
}

_BARBER: dict[Permission, Scope] = {
    P.APPOINTMENT_READ: S.OWN,
    P.APPOINTMENT_CREATE: S.OWN,
    P.APPOINTMENT_UPDATE: S.OWN,
    P.CLIENT_READ: S.OWN,
    P.TICKET_READ: S.OWN,
    P.COMMISSION_READ: S.OWN,
    P.CONVERSATION_READ: S.OWN,
    P.CATALOG_READ: S.UNIT,
    # No CANCEL: cancellations go through the front desk or management.
}

PERMISSIONS_BY_ROLE: dict[Role, dict[Permission, Scope]] = {
    Role.OWNER: _EVERYTHING,
    Role.MANAGER: _MANAGER,
    Role.RECEPTIONIST: _RECEPTIONIST,
    Role.BARBER: _BARBER,
}


def scope_for(role: Role, permission: Permission) -> Scope | None:
    """The role's scope for this permission, or None if the role lacks it."""
    return PERMISSIONS_BY_ROLE[role].get(permission)


def permissions_for(role: Role) -> dict[str, str]:
    """Serializable map so the frontend can build navigation and hide actions."""
    return {p.value: s.value for p, s in PERMISSIONS_BY_ROLE[role].items()}
