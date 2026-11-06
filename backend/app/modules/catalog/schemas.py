"""Request and response contracts of the catalog module."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field, StringConstraints


def _five_minute_steps(v: int) -> int:
    if v % 5:
        raise ValueError("a duração deve ser múltipla de 5 minutos")
    return v


Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=80)]
# An empty description is stored as no description.
Description = Annotated[
    str,
    StringConstraints(strip_whitespace=True, max_length=500),
    AfterValidator(lambda v: v or None),
]
Duration = Annotated[
    int,
    Field(ge=5, le=480, description="Minutes, in steps of 5"),
    AfterValidator(_five_minute_steps),
]
PriceCents = Annotated[int, Field(ge=0, le=10_000_000, description="Price in cents (BRL)")]


class ServiceIn(BaseModel):
    name: Name
    description: Description | None = None
    duration_minutes: Duration
    price_cents: PriceCents
    active: bool = True


class ServiceUpdate(BaseModel):
    """Partial: a field left out does not change. `description: null` clears it."""

    name: Name | None = None
    description: Description | None = None
    duration_minutes: Duration | None = None
    price_cents: PriceCents | None = None
    active: bool | None = None


class ServiceOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    duration_minutes: int
    price_cents: int
    active: bool
    barber_ids: list[uuid.UUID] = Field(description="Barbers who perform this service")
    created_at: datetime
    updated_at: datetime


class BarberServicesIn(BaseModel):
    service_ids: list[uuid.UUID] = Field(
        description="The full set of services the barber performs; replaces the current one"
    )
