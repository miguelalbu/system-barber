"""
Isolation invariants between shops.

If any of these break, one shop is seeing another shop's data. Do not relax any
of them without understanding exactly why.
"""

from tests.conftest import auth, core, create_shop, login

PASSWORD_A = "password-for-shop-a"
PASSWORD_B = "password-for-shop-b"
EMAIL = "same@email.com"


async def test_same_email_in_different_shops(client, core_key, slug):
    """
    Email is unique per shop, not globally. Two shops can have owners with the
    same email and independent passwords.
    """
    slug_a, slug_b = f"{slug}a", f"{slug}b"
    await create_shop(client, core_key, slug_a, EMAIL, PASSWORD_A)
    await create_shop(client, core_key, slug_b, EMAIL, PASSWORD_B)

    assert (await login(client, slug_a, EMAIL, PASSWORD_A)).status_code == 200
    assert (await login(client, slug_b, EMAIL, PASSWORD_B)).status_code == 200

    # One shop's password does not open the other.
    assert (await login(client, slug_a, EMAIL, PASSWORD_B)).status_code == 401
    assert (await login(client, slug_b, EMAIL, PASSWORD_A)).status_code == 401


async def test_token_does_not_cross_shops(client, core_key, slug):
    """A token we signed, but issued for another tenant, is worthless here."""
    slug_a, slug_b = f"{slug}a", f"{slug}b"
    await create_shop(client, core_key, slug_a, EMAIL, PASSWORD_A)
    await create_shop(client, core_key, slug_b, EMAIL, PASSWORD_B)

    token = (await login(client, slug_a, EMAIL, PASSWORD_A)).json()["access_token"]

    assert (await client.get("/auth/me", headers=auth(slug_a, token))).status_code == 200
    assert (await client.get("/auth/me", headers=auth(slug_b, token))).status_code == 403


async def test_team_only_sees_its_own_shop(client, core_key, slug):
    """No tenant filter in the code: the session only sees the shop's own schema."""
    slug_a, slug_b = f"{slug}a", f"{slug}b"
    await create_shop(client, core_key, slug_a, EMAIL, PASSWORD_A)
    await create_shop(client, core_key, slug_b, "other@email.com", PASSWORD_B)

    token = (await login(client, slug_a, EMAIL, PASSWORD_A)).json()["access_token"]
    team = (await client.get("/team", headers=auth(slug_a, token))).json()

    assert [m["email"] for m in team] == [EMAIL]


async def test_unknown_domain(client):
    resp = await client.get("/auth/me", headers={"X-Tenant-Slug": "shop-that-does-not-exist"})
    assert resp.status_code == 404


async def test_same_slug_never_creates_a_second_schema(client, core_key, slug):
    """Provisioning is idempotent by slug: a repeated request gets the existing job back."""
    first = await create_shop(client, core_key, slug, EMAIL, PASSWORD_A)
    resp = await client.post(
        "/core/tenants",
        headers=core(core_key),
        json={"slug": slug, "name": "Another", "owner": {"name": "Someone", "email": "x@y.com"}},
    )
    assert resp.status_code == 200
    assert resp.json()["tenant_id"] == first["tenant"]["id"]
