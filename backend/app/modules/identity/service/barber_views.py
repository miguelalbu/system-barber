"""
Read-only views of barbers for other modules (scheduling, later sales and
reports): who they are, where they work, whether they are active. Scope is the
caller module's job — these do not filter by user.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.repository import barbers as barber_repo


@dataclass(frozen=True)
class BarberInfo:
    id: uuid.UUID
    name: str
    unit_id: uuid.UUID
    active: bool


def _info(barber) -> BarberInfo:
    return BarberInfo(id=barber.id, name=barber.name, unit_id=barber.unit_id, active=barber.active)


async def barber_info(session: AsyncSession, barber_id: uuid.UUID) -> BarberInfo | None:
    barber = await barber_repo.get(session, barber_id)
    return None if barber is None else _info(barber)


async def list_barber_infos(
    session: AsyncSession,
    *,
    unit_ids: list[uuid.UUID] | None = None,
    active: bool | None = True,
) -> list[BarberInfo]:
    """Ordered by name. `unit_ids=None` means every unit."""
    barbers = await barber_repo.list_visible(session, unit_ids=unit_ids, active=active)
    return [_info(b) for b in barbers]
