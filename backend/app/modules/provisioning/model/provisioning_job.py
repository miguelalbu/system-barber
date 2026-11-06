import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.model_base import ControlBase, TimestampMixin, pg_enum, uuid_pk
from app.modules.provisioning.model.enums import JobStatus, JobStep


class ProvisioningJob(ControlBase, TimestampMixin):
    """
    The work of bringing a shop to life. `step` is where it is (or where it
    stopped); every step is idempotent, so `retry` simply runs again from there.
    """

    __tablename__ = "provisioning_jobs"

    id: Mapped[uuid.UUID] = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    # A curl retried before the first commit must not create a second shop.
    idempotency_key: Mapped[str | None] = mapped_column(String(120), unique=True)
    status: Mapped[JobStatus] = mapped_column(
        pg_enum(JobStatus, "job_status"), nullable=False, default=JobStatus.PENDING
    )
    step: Mapped[JobStep] = mapped_column(
        pg_enum(JobStep, "job_step"), nullable=False, default=JobStep.SCHEMA
    )
    # What the job needs to (re)run its steps: owner name/e-mail, unit name.
    # Never a secret — there is none in the contract.
    request: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    log: Mapped[str] = mapped_column(Text, nullable=False, default="")
    error: Mapped[str | None] = mapped_column(Text)
    # The first-access link, kept apart from the log (a secret mixed with
    # diagnostics gets copied while investigating) and erased on first read.
    setup_token_once: Mapped[str | None] = mapped_column(String(255))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
