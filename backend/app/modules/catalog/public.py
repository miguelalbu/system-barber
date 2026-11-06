"""
The only surface other modules may import from the catalog.

The scheduling module will read services (duration, price) through here.
"""

from app.modules.catalog.service.get_service import get_service

__all__ = ["get_service"]
