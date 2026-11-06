import enum


class TenantStatus(enum.StrEnum):
    TRIAL = "trial"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELED = "canceled"


class Role(enum.StrEnum):
    OWNER = "owner"
    MANAGER = "manager"
    RECEPTIONIST = "receptionist"
    BARBER = "barber"
