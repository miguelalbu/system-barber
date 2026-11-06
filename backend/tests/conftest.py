"""
Shared fixtures.

The suite runs against the development Postgres (port 5433) with the control
plane migrated (`make migrate`). Every shop a test creates goes through the
real path — control plane → provisioning job (schema, migrations, grants,
bootstrap) → owner's first-access invite — and is destroyed at the end of the
session: schema, role and catalog rows. Nothing is left behind.
"""

from __future__ import annotations

import asyncio
import secrets
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.database import engine
from app.core.security import hash_token
from app.main import app
from app.modules.provisioning.dependencies import READ_LIMIT, WRITE_LIMIT

ALL_SCOPES = ["tenant:read", "tenant:provision", "tenant:destroy"]

OWNER_EMAIL = "owner@barbershop.com"
OWNER_PASSWORD = "owner-password-123"
MEMBER_PASSWORD = "member-password-123"

# Slugs created during this run, destroyed at the end.
_created_slugs: set[str] = set()


def _migrator():
    return create_async_engine(settings.database_url_migrations, poolclass=NullPool)


async def _insert_core_key(raw: str, scopes: list[str], name: str) -> uuid.UUID:
    key_id = uuid.uuid4()
    eng = _migrator()
    async with eng.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO public.core_keys (id, name, key_hash, scopes, ip_allowlist) "
                "VALUES (:id, :name, :hash, :scopes, '{}')"
            ),
            {"id": key_id, "name": name, "hash": hash_token(raw), "scopes": scopes},
        )
    await eng.dispose()
    return key_id


async def _destroy_everything(slugs: set[str], key_ids: list[uuid.UUID]) -> None:
    eng = _migrator()
    async with eng.begin() as conn:
        for slug in slugs:
            schema = await conn.scalar(
                text("SELECT schema_name FROM public.tenants WHERE slug = :s"), {"s": slug}
            )
            if schema:
                await conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
                if await conn.scalar(
                    text("SELECT 1 FROM pg_roles WHERE rolname = :r"), {"r": schema}
                ):
                    await conn.execute(text(f'DROP OWNED BY "{schema}"'))
                    await conn.execute(text(f'DROP ROLE "{schema}"'))
            await conn.execute(text("DELETE FROM public.tenants WHERE slug = :s"), {"s": slug})
        for key_id in key_ids:
            await conn.execute(
                text("DELETE FROM public.core_audit_log WHERE core_key_id = :k"), {"k": key_id}
            )
            await conn.execute(text("DELETE FROM public.core_keys WHERE id = :k"), {"k": key_id})
    await eng.dispose()


_session_key_ids: list[uuid.UUID] = []


@pytest.fixture(scope="session")
def core_key() -> str:
    """A Core key with every scope, removed (with its audit trail) at the end."""
    raw = "nvc_test_" + secrets.token_urlsafe(24)
    _session_key_ids.append(asyncio.run(_insert_core_key(raw, ALL_SCOPES, "pytest")))
    yield raw
    asyncio.run(_destroy_everything(_created_slugs, _session_key_ids))


@pytest.fixture
def make_core_key():
    """Factory for keys with specific scopes; cleaned up with the session key."""

    async def factory(scopes: list[str], name: str = "pytest-scoped") -> tuple[str, uuid.UUID]:
        raw = "nvc_test_" + secrets.token_urlsafe(24)
        key_id = await _insert_core_key(raw, scopes, name)
        _session_key_ids.append(key_id)
        return raw, key_id

    return factory


@pytest.fixture(autouse=True)
async def _dispose_pool():
    """
    pytest-asyncio creates one event loop per test, and asyncpg connections stay
    bound to the loop they were created in. Without disposing the pool at the
    end of each test, the next one inherits connections from a closed loop.
    """
    yield
    await engine.dispose()


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    READ_LIMIT.reset()
    WRITE_LIMIT.reset()


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def slug() -> str:
    """A unique, valid slug per test."""
    return f"t{uuid.uuid4().hex[:10]}"


def core(key: str) -> dict[str, str]:
    return {"X-Core-Key": key}


def track(slug: str) -> None:
    """Register a slug created outside `provision`, so the session cleans it up."""
    _created_slugs.add(slug)


async def provision(
    client: AsyncClient,
    key: str,
    slug: str,
    owner_email: str,
    owner_name: str = "Test Owner",
    **extra,
) -> dict:
    """Provision a shop through the control plane; returns the detail (invite link once)."""
    _created_slugs.add(slug)
    resp = await client.post(
        "/core/tenants",
        headers=core(key),
        json={
            "slug": slug,
            "name": f"Barbearia {slug}",
            "owner": {"name": owner_name, "email": owner_email},
            **extra,
        },
    )
    assert resp.status_code == 202, resp.text
    detail = await client.get(f"/core/tenants/{resp.json()['tenant_id']}", headers=core(key))
    assert detail.status_code == 200, detail.text
    body = detail.json()
    assert body["status"] == "active", body
    return body


async def accept(client: AsyncClient, slug: str, invite_link: str, password: str):
    token = invite_link.rsplit("/", 1)[-1]
    return await client.post(
        "/team/invites/accept",
        headers={"X-Tenant-Slug": slug},
        json={"token": token, "password": password},
    )


async def create_shop(client: AsyncClient, key: str, slug: str, email: str, password: str) -> dict:
    """A ready shop: provisioned, with the owner's first access done."""
    detail = await provision(client, key, slug, email)
    accepted = await accept(client, slug, detail["invite_link"], password)
    assert accepted.status_code == 201, accepted.text
    return {"tenant": detail, "user": accepted.json()}


async def login(client: AsyncClient, slug: str, email: str, password: str):
    return await client.post(
        "/auth/login",
        headers={"X-Tenant-Slug": slug},
        json={"email": email, "password": password},
    )


def auth(slug: str, token: str) -> dict[str, str]:
    return {"X-Tenant-Slug": slug, "Authorization": f"Bearer {token}"}


async def owner_token(client: AsyncClient, core_key: str, slug: str) -> str:
    """A ready shop and its owner's access token."""
    await create_shop(client, core_key, slug, OWNER_EMAIL, OWNER_PASSWORD)
    return (await login(client, slug, OWNER_EMAIL, OWNER_PASSWORD)).json()["access_token"]


async def new_barber(
    client: AsyncClient, slug: str, token: str, name: str = "Diego Martins", **extra
):
    """Register a barber (no login) in the shop's first unit unless `unit_id` is given."""
    if "unit_id" not in extra:
        units = (await client.get("/tenant/units", headers=auth(slug, token))).json()
        extra["unit_id"] = units[0]["id"]
    resp = await client.post("/barbers", headers=auth(slug, token), json={"name": name, **extra})
    assert resp.status_code == 201, resp.text
    return resp.json()


async def member_token(
    client: AsyncClient,
    slug: str,
    token: str,
    *,
    role: str,
    email: str,
    unit_ids: list[str] | None = None,
    barber_id: str | None = None,
) -> str:
    """Invite someone with this role, accept the invite and return their access token."""
    body: dict = {"name": f"Member {role}", "email": email, "role": role}
    if unit_ids is not None:
        body["unit_ids"] = unit_ids
    if barber_id is not None:
        body["barber_id"] = barber_id
    created = await client.post("/team/invites", headers=auth(slug, token), json=body)
    assert created.status_code == 201, created.text
    accepted = await accept(client, slug, created.json()["link"], MEMBER_PASSWORD)
    assert accepted.status_code == 201, accepted.text
    return (await login(client, slug, email, MEMBER_PASSWORD)).json()["access_token"]


async def add_unit(slug: str, name: str) -> str:
    """A second unit, straight in the shop's schema (no route creates units yet)."""
    from app.core.database import tenant_session
    from app.modules.identity.model import Unit
    from app.modules.identity.public import schema_name_for

    async with tenant_session(schema_name_for(slug)) as session:
        unit = Unit(name=name)
        session.add(unit)
        await session.flush()
        return str(unit.id)
