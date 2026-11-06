"""Provisioning job, idempotency, first-access link, retry, reissue and destroy."""

from sqlalchemy import text

from app.core.database import migrator_engine
from app.modules.provisioning.service import run_provisioning_job as job_module
from tests.conftest import accept, core, create_shop, login, provision, track

OWNER = {"name": "Dono", "email": "dono@shop.com"}
PASSWORD = "owner-password-123"


async def _schema_exists(schema: str) -> bool:
    async with migrator_engine().connect() as conn:
        found = await conn.scalar(
            text("SELECT 1 FROM pg_namespace WHERE nspname = :n"), {"n": schema}
        )
        role = await conn.scalar(text("SELECT 1 FROM pg_roles WHERE rolname = :n"), {"n": schema})
    await migrator_engine().dispose()
    return bool(found), bool(role)


async def test_provisioning_builds_the_shop_and_delivers_the_link_once(client, core_key, slug):
    track(slug)
    resp = await client.post(
        "/core/tenants",
        headers=core(core_key),
        json={"slug": slug, "name": "Central", "owner": OWNER},
    )
    assert resp.status_code == 202
    tenant_id = resp.json()["tenant_id"]
    assert resp.headers["location"] == f"/core/tenants/{tenant_id}"

    first = (await client.get(f"/core/tenants/{tenant_id}", headers=core(core_key))).json()
    assert first["status"] == "active"
    assert first["schema_name"] == f"tenant_{slug}"
    assert first["schema_version"] == "t0001"
    assert first["job"]["status"] == "succeeded"
    assert first["invite_link"].endswith(first["invite_link"].rsplit("/", 1)[-1])
    assert await _schema_exists(f"tenant_{slug}") == (True, True)

    second = (await client.get(f"/core/tenants/{tenant_id}", headers=core(core_key))).json()
    assert second["invite_link"] is None  # erased on first read

    assert (await accept(client, slug, first["invite_link"], PASSWORD)).status_code == 201
    me = await login(client, slug, OWNER["email"], PASSWORD)
    assert me.status_code == 200


async def test_idempotency_key_returns_the_same_job(client, core_key, slug):
    track(slug)
    headers = {**core(core_key), "Idempotency-Key": f"idem-{slug}"}
    body = {"slug": slug, "name": "Central", "owner": OWNER}
    first = await client.post("/core/tenants", headers=headers, json=body)
    again = await client.post("/core/tenants", headers=headers, json={**body, "slug": f"{slug}x"})
    assert first.status_code == 202 and again.status_code == 200
    assert again.json()["job_id"] == first.json()["job_id"]


async def test_failed_job_keeps_the_schema_and_retry_resumes(client, core_key, slug, monkeypatch):
    track(slug)

    async def broken(schema: str) -> None:
        raise RuntimeError("grant step exploded")

    monkeypatch.setattr(job_module, "_step_grants", broken)
    resp = await client.post(
        "/core/tenants",
        headers=core(core_key),
        json={"slug": slug, "name": "Central", "owner": OWNER},
    )
    tenant_id = resp.json()["tenant_id"]
    failed = (await client.get(f"/core/tenants/{tenant_id}", headers=core(core_key))).json()
    assert failed["status"] == "failed"
    assert failed["job"]["step"] == "grants"
    assert "grant step exploded" in failed["job"]["error"]
    # Nothing is dropped on failure.
    assert (await _schema_exists(f"tenant_{slug}"))[0] is True

    monkeypatch.undo()
    retried = await client.post(f"/core/tenants/{tenant_id}/retry", headers=core(core_key))
    assert retried.status_code == 202
    done = (await client.get(f"/core/tenants/{tenant_id}", headers=core(core_key))).json()
    assert done["status"] == "active"
    assert done["invite_link"]

    again = await client.post(f"/core/tenants/{tenant_id}/retry", headers=core(core_key))
    assert again.status_code == 409


async def test_reissued_invite_replaces_the_old_one(client, core_key, slug):
    detail = await provision(client, core_key, slug, OWNER["email"])
    old = detail["invite_link"]

    reissued = await client.post(f"/core/tenants/{detail['id']}/invite", headers=core(core_key))
    assert reissued.status_code == 200
    new = reissued.json()["invite_link"]
    assert new != old

    assert (await accept(client, slug, old, PASSWORD)).status_code == 400
    assert (await accept(client, slug, new, PASSWORD)).status_code == 201

    # Once the owner is in, there is nothing to reissue.
    after = await client.post(f"/core/tenants/{detail['id']}/invite", headers=core(core_key))
    assert after.status_code == 409


async def test_destroy_needs_all_four_gates(client, core_key, make_core_key, slug):
    shop = await create_shop(client, core_key, slug, OWNER["email"], PASSWORD)
    tenant_id = shop["tenant"]["id"]
    url = f"/core/tenants/{tenant_id}"
    ok_body = {"confirm": slug, "exported": True}

    no_destroy_scope, _ = await make_core_key(["tenant:read", "tenant:provision"])
    assert (
        await client.request("DELETE", url, headers=core(no_destroy_scope), json=ok_body)
    ).status_code == 403
    assert (
        await client.request("DELETE", url, headers=core(core_key), json=ok_body)
    ).status_code == 409

    await client.post(f"{url}/suspend", headers=core(core_key))
    wrong = {"confirm": "other", "exported": True}
    assert (
        await client.request("DELETE", url, headers=core(core_key), json=wrong)
    ).status_code == 400
    not_exported = {"confirm": slug, "exported": False}
    assert (
        await client.request("DELETE", url, headers=core(core_key), json=not_exported)
    ).status_code == 400

    assert (
        await client.request("DELETE", url, headers=core(core_key), json=ok_body)
    ).status_code == 204
    assert await _schema_exists(f"tenant_{slug}") == (False, False)
    archived = (await client.get(url, headers=core(core_key))).json()
    assert archived["status"] == "archived"
    assert (await login(client, slug, OWNER["email"], PASSWORD)).status_code == 404
