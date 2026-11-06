import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.model_base import ControlBase, uuid_pk


class CoreAuditLog(ControlBase):
    """
    Every call to the control plane — denied ones included. The payload never
    carries secrets (passwords are dropped before they get here).
    """

    __tablename__ = "core_audit_log"
    __table_args__ = (Index("ix_core_audit_created", "created_at"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    # No FK: a revoked or deleted key must not erase its history.
    core_key_id: Mapped[uuid.UUID | None] = mapped_column(PgUUID(as_uuid=True))
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    target: Mapped[str | None] = mapped_column(String(120))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    result: Mapped[str] = mapped_column(String(40), nullable=False)
    ip: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
