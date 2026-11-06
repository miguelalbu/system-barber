import uuid

from sqlalchemy import ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.model_base import TenantBase, uuid_pk


class BarberService(TenantBase):
    """
    A service the barber performs. Not history: deleting either side drops the
    link. `barbers` belongs to identity — referenced by name, never imported.
    """

    __tablename__ = "barber_services"
    __table_args__ = (
        UniqueConstraint("barber_id", "service_id", name="uq_barber_service"),
        Index("ix_barber_service_service", "service_id"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    barber_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("barbers.id", ondelete="CASCADE"), nullable=False
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE"), nullable=False
    )
