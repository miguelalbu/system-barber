"""
The only surface other modules may import from clients.

The WhatsApp channel will find or create clients by phone through here.
"""

from app.modules.clients.phone import InvalidPhone, normalize_phone
from app.modules.clients.service.create_client import create_client

__all__ = ["InvalidPhone", "create_client", "normalize_phone"]
