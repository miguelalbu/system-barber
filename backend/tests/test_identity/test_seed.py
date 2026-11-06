"""Platform admin seeding: idempotency, validation and password rotation."""

import uuid

import pytest
from sqlalchemy import delete, select

from app.core.database import platform_session
from app.core.security import verify_password
from app.modules.identity.model import PlatformAdmin
from app.modules.identity.service.seed_platform_admin import (
    DEFAULT_NAME,
    SeedError,
    seed_platform_admin,
)

PASSWORD = "platform-password-123"


@pytest.fixture
def email() -> str:
    return f"admin-{uuid.uuid4().hex[:10]}@navalha.app"


@pytest.fixture(autouse=True)
async def _cleanup(email):
    yield
    async with platform_session() as session:
        await session.execute(delete(PlatformAdmin).where(PlatformAdmin.email == email))


async def _load(email: str) -> PlatformAdmin | None:
    async with platform_session() as session:
        return (
            await session.execute(select(PlatformAdmin).where(PlatformAdmin.email == email))
        ).scalar_one_or_none()


async def test_creates_account(email):
    action, generated = await seed_platform_admin(
        email=email, name="Miguel Albuquerque", password=PASSWORD
    )

    assert action == "created"
    assert generated is None  # nothing generated when a password was supplied

    admin = await _load(email)
    assert admin is not None
    assert admin.name == "Miguel Albuquerque"
    assert admin.active is True
    # The password is stored hashed, never in the clear.
    assert admin.password_hash != PASSWORD
    assert verify_password(PASSWORD, admin.password_hash)


async def test_generates_password_when_omitted(email):
    action, generated = await seed_platform_admin(email=email)

    assert action == "created"
    assert generated is not None
    assert len(generated) >= 20

    admin = await _load(email)
    assert admin is not None
    assert admin.name == DEFAULT_NAME
    assert verify_password(generated, admin.password_hash)


async def test_second_run_is_idempotent(email):
    await seed_platform_admin(email=email, name="Original", password=PASSWORD)

    action, generated = await seed_platform_admin(email=email, password="a-different-password")

    assert action == "unchanged"
    assert generated is None

    # Re-running the seed must never silently rotate a live credential.
    admin = await _load(email)
    assert admin is not None
    assert admin.name == "Original"
    assert verify_password(PASSWORD, admin.password_hash)


async def test_update_password_rotates(email):
    await seed_platform_admin(email=email, name="Original", password=PASSWORD)

    action, _ = await seed_platform_admin(
        email=email, password="rotated-password-456", update_password=True
    )

    assert action == "updated"
    admin = await _load(email)
    assert admin is not None
    assert verify_password("rotated-password-456", admin.password_hash)
    assert not verify_password(PASSWORD, admin.password_hash)
    # Omitting the name keeps the stored one, so a reset does not rename anyone.
    assert admin.name == "Original"


async def test_email_is_normalized(email):
    await seed_platform_admin(email=email.upper(), password=PASSWORD)
    assert await _load(email) is not None


async def test_rejects_short_password(email):
    with pytest.raises(SeedError, match="pelo menos 12"):
        await seed_platform_admin(email=email, password="short")


async def test_rejects_invalid_email():
    with pytest.raises(SeedError, match="inválido"):
        await seed_platform_admin(email="not-an-email", password=PASSWORD)
