import uuid
from collections.abc import Iterable
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.model import UnitException, UnitExceptionKind


async def get(session: AsyncSession, exception_id: uuid.UUID) -> UnitException | None:
    return await session.get(UnitException, exception_id, populate_existing=True)


async def list_between(
    session: AsyncSession,
    *,
    unit_ids: Iterable[uuid.UUID] | None,
    start: date,
    end: date,
    kind: UnitExceptionKind | None = None,
) -> list[UnitException]:
    """Exceptions touching [start, end]; `unit_ids=None` means every unit."""
    stmt = select(UnitException).where(
        UnitException.starts_on <= end, UnitException.ends_on >= start
    )
    if unit_ids is not None:
        stmt = stmt.where(UnitException.unit_id.in_(list(unit_ids)))
    if kind is not None:
        stmt = stmt.where(UnitException.kind == kind)
    order = (UnitException.starts_on, UnitException.unit_id)
    return list((await session.execute(stmt.order_by(*order))).scalars())
