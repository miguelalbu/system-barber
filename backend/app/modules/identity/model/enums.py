import enum


class TenantStatus(enum.StrEnum):
    """
    Operational lifecycle of a shop (DEC-013). Billing lives in the Core; only
    `active` is served.
    """

    PROVISIONING = "provisioning"
    ACTIVE = "active"
    FAILED = "failed"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class Role(enum.StrEnum):
    OWNER = "owner"
    MANAGER = "manager"
    RECEPTIONIST = "receptionist"
    BARBER = "barber"
