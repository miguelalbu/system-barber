import re
import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.clients.model import Client


def _like(term: str) -> str:
    """`%term%` with the user's `%`, `_` and `\\` taken literally."""
    return "%" + re.sub(r"([\\%_])", r"\\\1", term) + "%"


async def search(
    session: AsyncSession, *, q: str | None, active: bool | None, limit: int, offset: int
) -> tuple[list[Client], int]:
    """A page of clients by name, and the total of matches."""
    stmt = select(Client)
    if q:
        conditions = [Client.name.ilike(_like(q), escape="\\")]
        digits = re.sub(r"\D", "", q)
        if digits:
            conditions.append(Client.phone.contains(digits))
        stmt = stmt.where(or_(*conditions))
    if active is not None:
        stmt = stmt.where(Client.active.is_(active))

    total = (await session.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    page = stmt.order_by(func.lower(Client.name), Client.id).limit(limit).offset(offset)
    return list((await session.execute(page)).scalars()), total


async def get(session: AsyncSession, client_id: uuid.UUID) -> Client | None:
    """Fresh from the database (also reloads what a flush expired, like `updated_at`)."""
    stmt = select(Client).where(Client.id == client_id).execution_options(populate_existing=True)
    return (await session.execute(stmt)).scalar_one_or_none()


async def phone_taken(
    session: AsyncSession, phone: str, *, exclude_id: uuid.UUID | None = None
) -> bool:
    stmt = select(Client.id).where(Client.phone == phone)
    if exclude_id is not None:
        stmt = stmt.where(Client.id != exclude_id)
    return (await session.execute(stmt.limit(1))).first() is not None
