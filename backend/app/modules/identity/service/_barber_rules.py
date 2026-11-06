"""Rules shared by the barber registry actions (create, update) and invites."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequest, Conflict, Forbidden
from app.modules.identity.dependencies import AuthContext
from app.modules.identity.model import Barber, Role
from app.modules.identity.repository import barbers as barber_repo
from app.modules.identity.repository import units as unit_repo
from app.modules.identity.repository import users as user_repo
from app.modules.identity.schemas import BarberOut


def initials_of(name: str) -> str:
    """Label for a calendar column: "Diego Martins" → "DM", "Diego" → "DI"."""
    parts = [p for p in name.split() if p]
    if not parts:
        return "??"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def barber_out(barber: Barber) -> BarberOut:
    """The response shape. `barber.user` must be loaded (the repository does it)."""
    return BarberOut(
        id=barber.id,
        name=barber.name,
        initials=barber.initials,
        unit_id=barber.unit_id,
        default_commission=float(barber.default_commission),
        active=barber.active,
        user_id=barber.user_id,
        email=barber.user.email if barber.user else None,
        created_at=barber.created_at,
        updated_at=barber.updated_at,
    )


async def check_unit(session: AsyncSession, ctx: AuthContext, unit_id: uuid.UUID) -> None:
    """The unit exists and is one the caller manages."""
    if not await unit_repo.existing_ids(session, [unit_id]):
        raise BadRequest("Unidade inexistente")
    if not ctx.reaches_unit(unit_id):
        raise Forbidden("Você só pode cadastrar barbeiros nas unidades que administra")


async def check_linkable_user(
    session: AsyncSession, user_id: uuid.UUID, *, barber_id: uuid.UUID | None = None
) -> None:
    """An active login of this shop, not linked to another barber."""
    user = await user_repo.get(session, user_id)
    if user is None or not user.active:
        raise BadRequest("Usuário não encontrado ou inativo")
    linked = await barber_repo.find_by_user(session, user_id)
    if linked is not None and linked.id != barber_id:
        raise Conflict("Esse usuário já está ligado a outro barbeiro")


async def check_unlinkable(session: AsyncSession, user_id: uuid.UUID) -> None:
    """A `barber` login cannot lose its barber: its `own` scope filters by it."""
    user = await user_repo.get(session, user_id)
    if user is not None and user.role is Role.BARBER:
        raise Conflict("Um usuário com cargo de barbeiro precisa estar ligado a um barbeiro")
