"""
Units of the shop, their weekly opening hours and calendar exceptions
(holidays, closures, special hours) — spec S01.

Reading needs only a login and a linked unit; changing a unit is the owner's
(`tenant:configure`); hours and exceptions are `unit:configure` — the owner
everywhere, a manager in their units (PD-33).
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.modules.identity.dependencies import AuthContext, CurrentUser, SessionDep, require
from app.modules.identity.model import Unit, UnitException
from app.modules.identity.permissions import Permission
from app.modules.identity.schemas import (
    HolidayOut,
    UnitExceptionIn,
    UnitExceptionOut,
    UnitExceptionUpdate,
    UnitIn,
    UnitOut,
    UnitUpdate,
    WeeklyHoursIn,
    WeeklyHoursOut,
)
from app.modules.identity.service.create_unit import create_unit
from app.modules.identity.service.create_unit_exceptions import create_unit_exceptions
from app.modules.identity.service.delete_unit import delete_unit
from app.modules.identity.service.delete_unit_exception import delete_unit_exception
from app.modules.identity.service.get_unit import get_unit
from app.modules.identity.service.get_unit_hours import get_unit_hours
from app.modules.identity.service.list_holidays import list_holidays
from app.modules.identity.service.list_unit_exceptions import list_unit_exceptions
from app.modules.identity.service.list_units import list_units
from app.modules.identity.service.set_unit_hours import set_unit_hours
from app.modules.identity.service.update_unit import update_unit
from app.modules.identity.service.update_unit_exception import update_unit_exception

router = APIRouter(prefix="/tenant", tags=["shop"])

Configure = Annotated[AuthContext, Depends(require(Permission.TENANT_CONFIGURE))]
ConfigureUnit = Annotated[AuthContext, Depends(require(Permission.UNIT_CONFIGURE))]


# --- Units ----------------------------------------------------------------- #


@router.get("/units", response_model=list[UnitOut], summary="Visible units")
async def units(ctx: CurrentUser, session: SessionDep, active: bool | None = None) -> list[Unit]:
    return await list_units(session, ctx, active=active)


@router.post(
    "/units", response_model=UnitOut, status_code=status.HTTP_201_CREATED, summary="New unit"
)
async def create(data: UnitIn, _: Configure, session: SessionDep) -> Unit:
    """Born open Monday to Saturday, 09:00–19:00 (editable)."""
    return await create_unit(session, data)


@router.get("/units/{unit_id}", response_model=UnitOut, summary="One unit")
async def one(unit_id: uuid.UUID, ctx: CurrentUser, session: SessionDep) -> Unit:
    return await get_unit(session, ctx, unit_id)


@router.patch("/units/{unit_id}", response_model=UnitOut, summary="Update a unit")
async def update(unit_id: uuid.UUID, data: UnitUpdate, _: Configure, session: SessionDep) -> Unit:
    """409 when deactivating the last active unit or one with active barbers."""
    return await update_unit(session, unit_id, data)


@router.delete(
    "/units/{unit_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a unit without history",
)
async def delete(unit_id: uuid.UUID, _: Configure, session: SessionDep) -> None:
    """409 with history, users linked to it, or when it is the last active unit."""
    await delete_unit(session, unit_id)


# --- Weekly hours ---------------------------------------------------------- #


@router.get("/units/{unit_id}/hours", response_model=WeeklyHoursOut, summary="Weekly hours")
async def hours(unit_id: uuid.UUID, ctx: CurrentUser, session: SessionDep) -> WeeklyHoursOut:
    return await get_unit_hours(session, ctx, unit_id)


@router.put("/units/{unit_id}/hours", response_model=WeeklyHoursOut, summary="Replace the week")
async def set_hours(
    unit_id: uuid.UUID, data: WeeklyHoursIn, ctx: ConfigureUnit, session: SessionDep
) -> WeeklyHoursOut:
    """All 7 days, 0–3 intervals each; a day without intervals is closed."""
    return await set_unit_hours(session, ctx, unit_id, data)


# --- Calendar exceptions ---------------------------------------------------- #


@router.get(
    "/unit-exceptions", response_model=list[UnitExceptionOut], summary="Holidays and closures"
)
async def exceptions(
    ctx: CurrentUser,
    session: SessionDep,
    unit_id: uuid.UUID | None = None,
    from_: Annotated[date | None, Query(alias="from")] = None,
    to: date | None = None,
) -> list[UnitException]:
    """Touching the period; default from today to 365 days ahead."""
    return await list_unit_exceptions(session, ctx, unit_id=unit_id, start=from_, end=to)


@router.post(
    "/unit-exceptions",
    response_model=list[UnitExceptionOut],
    status_code=status.HTTP_201_CREATED,
    summary="Close or open specially on dates",
)
async def create_exceptions(
    data: UnitExceptionIn, ctx: ConfigureUnit, session: SessionDep
) -> list[UnitException]:
    """One per unit in `unit_ids`, all or nothing. Overlap in a unit → 409."""
    return await create_unit_exceptions(session, ctx, data)


@router.patch(
    "/unit-exceptions/{exception_id}", response_model=UnitExceptionOut, summary="Edit an exception"
)
async def update_exception(
    exception_id: uuid.UUID, data: UnitExceptionUpdate, ctx: ConfigureUnit, session: SessionDep
) -> UnitException:
    return await update_unit_exception(session, ctx, exception_id, data)


@router.delete(
    "/unit-exceptions/{exception_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an exception",
)
async def delete_exception(
    exception_id: uuid.UUID, ctx: ConfigureUnit, session: SessionDep
) -> None:
    await delete_unit_exception(session, ctx, exception_id)


@router.get("/holidays", response_model=list[HolidayOut], summary="Suggested national holidays")
async def holidays(
    ctx: CurrentUser, session: SessionDep, year: Annotated[int, Query(ge=2000, le=2100)]
) -> list[HolidayOut]:
    """Nothing closes by itself: the panel creates the closures the user picks."""
    return await list_holidays(session, ctx, year)
