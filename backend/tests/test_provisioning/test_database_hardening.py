"""What the database itself refuses (doc Camada 3), and where shop data physically lives."""

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError

from app.core.database import control_session, engine, migrator_engine, tenant_session
from app.modules.identity.model import User
from tests.conftest import create_shop

EMAIL = "owner@shop.com"
PASSWORD = "owner-password-123"


async def test_shop_data_lives_only_in_its_schema(client, core_key, slug):
    await create_shop(client, core_key, slug, EMAIL, PASSWORD)
    async with migrator_engine().connect() as conn:
        tables = set(
            (
                await conn.execute(
                    text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = 'public'"
                    )
                )
            ).scalars()
        )
        in_schema = await conn.scalar(text(f'SELECT count(*) FROM "tenant_{slug}".users'))
    await migrator_engine().dispose()

    assert "users" not in tables and "units" not in tables
    assert in_schema == 1


async def test_runtime_role_has_no_ddl(client, core_key, slug):
    await create_shop(client, core_key, slug, EMAIL, PASSWORD)
    for target in ("public.evil", f'"tenant_{slug}".evil'):
        with pytest.raises(DBAPIError, match="permission denied"):
            async with engine.begin() as conn:
                await conn.execute(text(f"CREATE TABLE {target} (id int)"))


async def test_shop_role_cannot_reach_the_control_plane(client, core_key, slug):
    await create_shop(client, core_key, slug, EMAIL, PASSWORD)
    async with migrator_engine().connect() as conn:
        await conn.execute(text(f'SET ROLE "tenant_{slug}"'))
        assert await conn.scalar(text(f'SELECT count(*) FROM "tenant_{slug}".users')) == 1
        with pytest.raises(DBAPIError, match="permission denied"):
            await conn.execute(text("SELECT * FROM public.tenants"))
    await migrator_engine().dispose()


async def test_shop_tables_are_unreachable_without_a_tenant_session(client, core_key, slug):
    """No search_path anywhere: outside a tenant session, shop tables simply do not exist."""
    await create_shop(client, core_key, slug, EMAIL, PASSWORD)

    # The placeholder schema `tenant` is never translated here, so the SQL names
    # a relation that does not exist — it can never fall through to `public`.
    with pytest.raises(DBAPIError, match=r'relation "tenant\.users" does not exist'):
        async with control_session() as session:
            await session.execute(select(User))

    async with tenant_session(f"tenant_{slug}") as session:
        assert [u.email for u in (await session.scalars(select(User)))] == [EMAIL]
