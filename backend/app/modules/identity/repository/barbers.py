import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.identity.model import Barber


async def id_for_user(session: AsyncSession, user_id: uuid.UUID) -> uuid.UUID | None:
    return (
        await session.execute(select(Barber.id).where(Barber.user_id == user_id))
    ).scalar_one_or_none()


async def ids_by_user(session: AsyncSession) -> dict[uuid.UUID, uuid.UUID]:
    """user_id → barber_id for every barber linked to a login."""
    rows = await session.execute(
        select(Barber.user_id, Barber.id).where(Barber.user_id.is_not(None))
    )
    return dict(rows.all())


async def list_visible(
    session: AsyncSession,
    *,
    unit_ids: list[uuid.UUID] | None,
    unit_id: uuid.UUID | None = None,
    active: bool | None = None,
) -> list[Barber]:
    """Barbers ordered by name, with their login. `unit_ids=None` means every unit."""
    stmt = select(Barber).options(selectinload(Barber.user))
    if unit_ids is not None:
        stmt = stmt.where(Barber.unit_id.in_(unit_ids))
    if unit_id is not None:
        stmt = stmt.where(Barber.unit_id == unit_id)
    if active is not None:
        stmt = stmt.where(Barber.active.is_(active))
    return list((await session.execute(stmt.order_by(func.lower(Barber.name)))).scalars())


async def get(session: AsyncSession, barber_id: uuid.UUID) -> Barber | None:
    """
    Fresh from the database, with its login. `populate_existing` also reloads
    what a flush expired (`updated_at`), so call it only after flushing changes.
    """
    stmt = (
        select(Barber)
        .options(selectinload(Barber.user))
        .where(Barber.id == barber_id)
        .execution_options(populate_existing=True)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def find_by_user(session: AsyncSession, user_id: uuid.UUID) -> Barber | None:
    return (
        await session.execute(select(Barber).where(Barber.user_id == user_id))
    ).scalar_one_or_none()
