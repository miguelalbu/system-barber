import enum


class CoreScope(enum.StrEnum):
    """What a Core key may do. Destroying is a separate scope on purpose."""

    TENANT_READ = "tenant:read"
    TENANT_PROVISION = "tenant:provision"
    TENANT_DESTROY = "tenant:destroy"


class JobStatus(enum.StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class JobStep(enum.StrEnum):
    """Provisioning steps, in order. Each one is idempotent, so a retry resumes."""

    SCHEMA = "schema"
    MIGRATIONS = "migrations"
    GRANTS = "grants"
    BOOTSTRAP = "bootstrap"
    ACTIVATE = "activate"
    DONE = "done"
