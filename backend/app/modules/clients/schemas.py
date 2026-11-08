"""Request and response contracts of the clients module."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, EmailStr, Field, StringConstraints

from app.core.phone import normalize_phone


def _not_in_the_future(v: date) -> date:
    if v > date.today():
        raise ValueError("a data de nascimento não pode estar no futuro")
    return v


Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=120)]
Phone = Annotated[
    str,
    StringConstraints(strip_whitespace=True, max_length=32),
    AfterValidator(normalize_phone),
    Field(description="Any common format; stored and returned in E.164"),
]
BirthDate = Annotated[date, AfterValidator(_not_in_the_future)]
# An empty note is stored as no note.
Notes = Annotated[
    str,
    StringConstraints(strip_whitespace=True, max_length=1000),
    AfterValidator(lambda v: v or None),
]
Email = Annotated[EmailStr, AfterValidator(str.lower)]


class ClientIn(BaseModel):
    name: Name
    phone: Phone
    email: Email | None = None
    birth_date: BirthDate | None = None
    notes: Notes | None = None
    active: bool = True


class ClientUpdate(BaseModel):
    """Partial: a field left out does not change. `null` clears the optional fields."""

    name: Name | None = None
    phone: Phone | None = None
    email: Email | None = None
    birth_date: BirthDate | None = None
    notes: Notes | None = None
    active: bool | None = None


class ClientOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    phone: str = Field(description="E.164")
    email: str | None
    birth_date: date | None
    notes: str | None
    active: bool
    created_at: datetime
    updated_at: datetime


class ClientPage(BaseModel):
    items: list[ClientOut]
    total: int = Field(description="Matches across every page")
