from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.clients.repository import clients as client_repo
from app.modules.clients.schemas import ClientOut, ClientPage
from app.modules.identity.public import AuthContext, Scope


async def list_clients(
    session: AsyncSession,
    ctx: AuthContext,
    *,
    q: str | None,
    active: bool | None,
    limit: int,
    offset: int,
) -> ClientPage:
    """
    `all` and `unit` see every client — a client belongs to the shop, not to a
    unit (spec P3). `own` (a barber) sees the clients they served: until the
    scheduling module exists there is no such record, so the page is empty.
    """
    if ctx.scope is Scope.OWN:
        return ClientPage(items=[], total=0)
    clients, total = await client_repo.search(
        session, q=(q or "").strip() or None, active=active, limit=limit, offset=offset
    )
    return ClientPage(items=[ClientOut.model_validate(c) for c in clients], total=total)
