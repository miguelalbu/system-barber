import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.core.model_base import ControlBase, uuid_pk


class CoreKey(ControlBase):
    """
    Credential of the platform Core. Only the SHA-256 is stored; the raw value
    is shown once by the CLI that creates it (`app/management/core_key.py`).
    """

    __tablename__ = "core_keys"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    scopes: Mapped[list[str]] = mapped_column(ARRAY(String(40)), nullable=False, default=list)
    # Empty = any address. Only the Core calls the control plane.
    ip_allowlist: Mapped[list[str]] = mapped_column(ARRAY(String(64)), nullable=False, default=list)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
