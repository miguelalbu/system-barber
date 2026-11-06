"""Invites: described without being spent, accepted exactly once — even concurrently."""

import asyncio

from app.modules.identity.service import login as login_module
from tests.conftest import accept, auth, create_shop, login

EMAIL = "owner@shop.com"
PASSWORD = "owner-password-123"


async def _team_invite(client, slug, owner_token, email="new@shop.com"):
    created = await client.post(
        "/team/invites",
        headers=auth(slug, owner_token),
        json={"name": "Nova Pessoa", "email": email, "role": "receptionist"},
    )
    assert created.status_code == 201, created.text
    return created.json()["link"]


async def test_lookup_describes_without_spending(client, core_key, slug):
    await create_shop(client, core_key, slug, EMAIL, PASSWORD)
    owner = (await login(client, slug, EMAIL, PASSWORD)).json()["access_token"]
    link = await _team_invite(client, slug, owner)
    token = link.rsplit("/", 1)[-1]

    for _ in range(2):
        described = await client.post(
            "/team/invites/lookup", headers={"X-Tenant-Slug": slug}, json={"token": token}
        )
        assert described.status_code == 200
        assert described.json()["email"] == "new@shop.com"
        assert described.json()["role"] == "receptionist"

    assert (await accept(client, slug, link, "new-password-123")).status_code == 201
    spent = await client.post(
        "/team/invites/lookup", headers={"X-Tenant-Slug": slug}, json={"token": token}
    )
    assert spent.status_code == 400


async def test_concurrent_accepts_create_one_login(client, core_key, slug):
    await create_shop(client, core_key, slug, EMAIL, PASSWORD)
    owner = (await login(client, slug, EMAIL, PASSWORD)).json()["access_token"]
    link = await _team_invite(client, slug, owner)

    results = await asyncio.gather(
        accept(client, slug, link, "first-password-123"),
        accept(client, slug, link, "second-password-123"),
    )
    assert sorted(r.status_code for r in results) == [201, 400]

    team = (await client.get("/team", headers=auth(slug, owner))).json()
    assert [m["email"] for m in team].count("new@shop.com") == 1


async def test_invite_of_one_shop_is_worthless_in_another(client, core_key, slug):
    await create_shop(client, core_key, f"{slug}a", EMAIL, PASSWORD)
    await create_shop(client, core_key, f"{slug}b", EMAIL, PASSWORD)
    owner_a = (await login(client, f"{slug}a", EMAIL, PASSWORD)).json()["access_token"]
    link = await _team_invite(client, f"{slug}a", owner_a)

    assert (await accept(client, f"{slug}b", link, "some-password-123")).status_code == 400


async def test_unknown_email_costs_a_password_check(client, core_key, slug, monkeypatch):
    """Without the dummy hash, a miss answers faster than a hit and the login can be timed."""
    await create_shop(client, core_key, slug, EMAIL, PASSWORD)
    checked: list[str] = []
    real = login_module.verify_password

    def spy(password: str, password_hash: str) -> bool:
        checked.append(password_hash)
        return real(password, password_hash)

    monkeypatch.setattr(login_module, "verify_password", spy)
    resp = await login(client, slug, "nobody@shop.com", "whatever-123")

    assert resp.status_code == 401
    assert resp.json()["detail"] == "E-mail ou senha inválidos"
    assert checked == [login_module.DUMMY_HASH]
