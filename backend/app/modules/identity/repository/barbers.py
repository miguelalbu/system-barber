import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
