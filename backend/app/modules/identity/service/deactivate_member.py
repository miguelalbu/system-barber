from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequest, Forbidden, NotFound
from app.modules.identity.dependencies import AuthContext
from app.modules.identity.model import Role
from app.modules.identity.repository import users as user_repo


async def deactivate_member(session: AsyncSession, ctx: AuthContext, user_id: uuid.UUID) -> None:
    """
    Deactivate rather than delete: the appointment and commission history has to
    keep pointing at a real person.
    """
    if user_id == ctx.user.id:
        raise BadRequest("Você não pode desativar a si mesmo")

    user = await user_repo.get(session, user_id)
    if user is None:
        raise NotFound("Usuário não encontrado")
    if user.role is Role.OWNER:
        raise Forbidden("O dono não pode ser desativado")

    user.active = False
