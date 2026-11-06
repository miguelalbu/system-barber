import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.model import User, UserUnit


async def get(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await session.get(User, user_id)


async def find_by_email(session: AsyncSession, email: str) -> User | None:
    return (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()


async def email_taken(session: AsyncSession, email: str) -> bool:
    found = (await session.execute(select(User.id).where(User.email == email))).scalar_one_or_none()
    return found is not None


async def list_members(session: AsyncSession, *, unit_ids: list[uuid.UUID] | None) -> list[User]:
    """Members ordered by name. `unit_ids=None` means the whole shop."""
    stmt = select(User).order_by(User.name)
    if unit_ids is not None:
        stmt = stmt.where(
            User.id.in_(select(UserUnit.user_id).where(UserUnit.unit_id.in_(unit_ids)))
        )
    return list((await session.execute(stmt)).scalars())


async def unit_ids_of(session: AsyncSession, user_id: uuid.UUID) -> list[uuid.UUID]:
    return list(
        (
            await session.execute(select(UserUnit.unit_id).where(UserUnit.user_id == user_id))
        ).scalars()
    )
