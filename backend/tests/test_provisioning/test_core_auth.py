"""The control plane's own credential: X-Core-Key, scopes, audit, rate limit."""

from sqlalchemy import text

from app.core.database import migrator_engine
from app.modules.provisioning.dependencies import WRITE_LIMIT
from tests.conftest import core, track

BODY = {"name": "Barbearia", "owner": {"name": "Dono", "email": "dono@shop.com"}}


async def _audit_rows(where: str, params: dict) -> list[dict]:
    async with migrator_engine().connect() as conn:
        rows = (
            (await conn.execute(text(f"SELECT * FROM public.core_audit_log WHERE {where}"), params))
            .mappings()
            .all()
        )
    await migrator_engine().dispose()
    return [dict(r) for r in rows]


async def test_missing_unknown_and_revoked_keys_are_indistinguishable(client, make_core_key):
    raw, key_id = await make_core_key(["tenant:read"])
    async with migrator_engine().begin() as conn:
        await conn.execute(
            text("UPDATE public.core_keys SET revoked_at = now() WHERE id = :k"), {"k": key_id}
        )
    await migrator_engine().dispose()

    answers = [
        await client.get("/core/tenants"),
        await client.get("/core/tenants", headers=core("nvc_not_a_real_key")),
        await client.get("/core/tenants", headers=core(raw)),
    ]
    assert {r.status_code for r in answers} == {401}
    assert len({r.json()["detail"] for r in answers}) == 1


async def test_scope_is_enforced(client, make_core_key, slug):
    reader, _ = await make_core_key(["tenant:read"])
    resp = await client.post("/core/tenants", headers=core(reader), json={"slug": slug, **BODY})
    assert resp.status_code == 403
    assert "tenant:provision" in resp.json()["detail"]


async def test_ip_allowlist(client, make_core_key):
    raw, key_id = await make_core_key(["tenant:read"])
    async with migrator_engine().begin() as conn:
        await conn.execute(
            text("UPDATE public.core_keys SET ip_allowlist = '{10.0.0.1}' WHERE id = :k"),
            {"k": key_id},
        )
    await migrator_engine().dispose()
    assert (await client.get("/core/tenants", headers=core(raw))).status_code == 403


async def test_every_call_is_audited_including_denied(client, make_core_key):
    raw, key_id = await make_core_key(["tenant:read"])
    await client.get("/core/tenants", headers=core(raw))
    await client.post("/core/tenants", headers=core(raw), json={"slug": "zz-denied", **BODY})

    results = sorted(r["result"] for r in await _audit_rows("core_key_id = :k", {"k": key_id}))
    assert results == ["denied:403", "ok"]


async def test_password_in_the_body_is_dropped_and_never_audited(client, core_key, slug):
    track(slug)
    resp = await client.post(
        "/core/tenants",
        headers=core(core_key),
        json={
            "slug": slug,
            **BODY,
            "password": "super-secret-123",
            "owner": {**BODY["owner"], "password": "x-secret-9"},
        },
    )
    assert resp.status_code == 202
    rows = await _audit_rows("target = :t", {"t": slug})
    assert rows and all("secret" not in str(r["payload"]) for r in rows)


async def test_mutations_are_rate_limited(client, make_core_key, monkeypatch):
    raw, _ = await make_core_key(["tenant:provision"])
    monkeypatch.setattr(WRITE_LIMIT, "limit", 2)
    codes = [
        (
            await client.post("/core/tenants", headers=core(raw), json={"slug": "ab", **BODY})
        ).status_code
        for _ in range(3)
    ]
    assert codes == [422, 422, 429]


async def test_control_plane_is_out_of_the_public_docs(client, core_key):
    public = (await client.get("/openapi.json")).json()
    assert not any(path.startswith("/core") for path in public["paths"])

    assert (await client.get("/core/openapi.json")).status_code == 401
    private = (await client.get("/core/openapi.json", headers=core(core_key))).json()
    assert "/core/tenants" in private["paths"]
    provision_body = private["components"]["schemas"]["ProvisionIn"]["properties"]
    assert "password" not in provision_body
