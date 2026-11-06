from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.dependencies import AuthContext
from app.modules.identity.repository import barbers as barber_repo
from app.modules.identity.repository import users as user_repo
from app.modules.identity.schemas import MemberOut


async def list_members(session: AsyncSession, ctx: AuthContext) -> list[MemberOut]:
    # RLS already limits us to the tenant; here we only apply the unit scope.
    users = await user_repo.list_members(session, unit_ids=ctx.unit_filter)
    links = await barber_repo.ids_by_user(session)
    return [
        MemberOut.model_validate(u).model_copy(update={"barber_id": links.get(u.id)}) for u in users
    ]
