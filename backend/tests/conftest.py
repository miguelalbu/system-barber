import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import engine
from app.main import app


@pytest.fixture(autouse=True)
async def _dispose_pool():
    """
    pytest-asyncio creates one event loop per test, and asyncpg connections stay
    bound to the loop they were created in. Without disposing the pool at the
    end of each test, the next one inherits connections from a closed loop.
    """
    yield
    await engine.dispose()


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def slug() -> str:
    """A unique slug per test — tests run against the development database."""
    return f"t{uuid.uuid4().hex[:10]}"


async def create_shop(client: AsyncClient, slug: str, email: str, password: str) -> dict:
    resp = await client.post(
        "/auth/register-shop",
        json={
            "shop_name": f"Barbearia {slug}",
            "slug": slug,
            "owner_name": "Test Owner",
            "email": email,
            "password": password,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def login(client: AsyncClient, slug: str, email: str, password: str):
    return await client.post(
        "/auth/login",
        headers={"X-Tenant-Slug": slug},
        json={"email": email, "password": password},
    )


def auth(slug: str, token: str) -> dict[str, str]:
    return {"X-Tenant-Slug": slug, "Authorization": f"Bearer {token}"}
