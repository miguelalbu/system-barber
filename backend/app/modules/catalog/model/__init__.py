"""Catalog tables, per shop (`TenantBase`). Importing this registers them."""

from app.modules.catalog.model.barber_service import BarberService
from app.modules.catalog.model.service import Service

__all__ = ["BarberService", "Service"]
