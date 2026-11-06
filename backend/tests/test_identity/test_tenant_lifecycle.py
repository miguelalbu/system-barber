"""Only an active shop whose schema is not behind is served (DEC-013)."""

from sqlalchemy import text

from app.core import schema_version
from app.core.database import migrator_engine
from tests.conftest import auth, core, create_shop, login

EMAIL = "owner@shop.com"
PASSWORD = "owner-password-123"


async def _set_status(slug: str, status: str) -> None:
    async with migrator_engine().begin() as conn:
        await conn.execute(
            text("UPDATE public.tenants SET status = :st WHERE slug = :s"),
            {"st": status, "s": slug},
        )
    await migrator_engine().dispose()


async def test_suspended_shop_refuses_even_the_right_password(client, core_key, slug):
    shop = await create_shop(client, core_key, slug, EMAIL, PASSWORD)
    token = (await login(client, slug, EMAIL, PASSWORD)).json()["access_token"]

    suspended = await client.post(
        f"/core/tenants/{shop['tenant']['id']}/suspend", headers=core(core_key)
    )
    assert suspended.json()["status"] == "suspended"

    denied = await login(client, slug, EMAIL, PASSWORD)
    assert denied.status_code == 403
    assert denied.json()["detail"] == "Assinatura inativa"
    # A token issued before the suspension stops working at once, not when it expires.
    assert (await client.get("/auth/me", headers=auth(slug, token))).status_code == 403

    await client.post(f"/core/tenants/{shop['tenant']['id']}/resume", headers=core(core_key))
    assert (await login(client, slug, EMAIL, PASSWORD)).status_code == 200


async def test_shop_not_ready_answers_503(client, core_key, slug):
    await create_shop(client, core_key, slug, EMAIL, PASSWORD)
    for status in ("provisioning", "failed"):
        await _set_status(slug, status)
        resp = await login(client, slug, EMAIL, PASSWORD)
        assert resp.status_code == 503, status


async def test_archived_shop_looks_unknown(client, core_key, slug):
    await create_shop(client, core_key, slug, EMAIL, PASSWORD)
    await _set_status(slug, "archived")
    resp = await login(client, slug, EMAIL, PASSWORD)
    assert resp.status_code == 404
    assert "não encontrada" in resp.json()["detail"]


async def test_schema_behind_the_build_is_not_served(client, core_key, slug, monkeypatch):
    await create_shop(client, core_key, slug, EMAIL, PASSWORD)
    # Pretend this build expects a newer revision than the one the shop has.
    monkeypatch.setattr(schema_version, "_older_than_head", lambda: frozenset({"t0001"}))

    resp = await login(client, slug, EMAIL, PASSWORD)
    assert resp.status_code == 503
    assert "manutenção" in resp.json()["detail"]


def test_only_behind_is_refused(monkeypatch):
    monkeypatch.setattr(schema_version, "_older_than_head", lambda: frozenset({"t0001"}))
    assert schema_version.is_behind("t0001") is True
    assert schema_version.is_behind(None) is False  # never recorded: not punished
    assert schema_version.is_behind("t0099") is False  # ahead (rolling deploy): served
