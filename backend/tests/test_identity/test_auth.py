"""Login, refresh rotation, team invites and RBAC boundaries."""

from tests.conftest import auth, create_shop, login

PASSWORD = "owner-password-123"
EMAIL = "owner@barbershop.com"

BARBER_EMAIL = "diego@barbershop.com"
BARBER_PASSWORD = "diego-password-123"


async def _invite_barber(client, slug, owner_token) -> str:
    """Invites Diego as a barber, accepts it, and returns his access token."""
    created = await client.post(
        "/team/invites",
        headers=auth(slug, owner_token),
        json={"name": "Diego Martins", "email": BARBER_EMAIL, "role": "barber"},
    )
    assert created.status_code == 201, created.text
    invite_token = created.json()["link"].rsplit("/", 1)[-1]

    accepted = await client.post(
        "/team/invites/accept",
        headers={"X-Tenant-Slug": slug},
        json={"token": invite_token, "password": BARBER_PASSWORD},
    )
    assert accepted.status_code == 201, accepted.text
    return (await login(client, slug, BARBER_EMAIL, BARBER_PASSWORD)).json()["access_token"]


async def test_me_returns_role_permissions(client, core_key, slug):
    await create_shop(client, core_key, slug, EMAIL, PASSWORD)
    token = (await login(client, slug, EMAIL, PASSWORD)).json()["access_token"]

    body = (await client.get("/auth/me", headers=auth(slug, token))).json()

    assert body["user"]["role"] == "owner"
    assert body["all_units"] is True
    # The owner has every permission, all at full scope.
    assert set(body["permissions"].values()) == {"all"}


async def test_wrong_password(client, core_key, slug):
    await create_shop(client, core_key, slug, EMAIL, PASSWORD)
    assert (await login(client, slug, EMAIL, "guess")).status_code == 401


async def test_no_token(client, core_key, slug):
    await create_shop(client, core_key, slug, EMAIL, PASSWORD)
    assert (await client.get("/auth/me", headers={"X-Tenant-Slug": slug})).status_code == 401


async def test_refresh_rotates_and_invalidates_previous(client, core_key, slug):
    await create_shop(client, core_key, slug, EMAIL, PASSWORD)
    first = (await login(client, slug, EMAIL, PASSWORD)).json()["refresh_token"]

    resp = await client.post(
        "/auth/refresh", headers={"X-Tenant-Slug": slug}, json={"refresh_token": first}
    )
    assert resp.status_code == 200
    second = resp.json()["refresh_token"]
    assert second != first

    # The token just used dies on rotation.
    reuse = await client.post(
        "/auth/refresh", headers={"X-Tenant-Slug": slug}, json={"refresh_token": first}
    )
    assert reuse.status_code == 401


async def test_logout_revokes(client, core_key, slug):
    await create_shop(client, core_key, slug, EMAIL, PASSWORD)
    refresh = (await login(client, slug, EMAIL, PASSWORD)).json()["refresh_token"]

    out = await client.post(
        "/auth/logout", headers={"X-Tenant-Slug": slug}, json={"refresh_token": refresh}
    )
    assert out.status_code == 204

    after = await client.post(
        "/auth/refresh", headers={"X-Tenant-Slug": slug}, json={"refresh_token": refresh}
    )
    assert after.status_code == 401


async def test_invite_creates_barber_with_calendar(client, core_key, slug):
    await create_shop(client, core_key, slug, EMAIL, PASSWORD)
    owner = (await login(client, slug, EMAIL, PASSWORD)).json()["access_token"]

    created = await client.post(
        "/team/invites",
        headers=auth(slug, owner),
        json={"name": "Diego Martins", "email": BARBER_EMAIL, "role": "barber"},
    )
    assert created.status_code == 201
    invite_token = created.json()["link"].rsplit("/", 1)[-1]

    accepted = await client.post(
        "/team/invites/accept",
        headers={"X-Tenant-Slug": slug},
        json={"token": invite_token, "password": BARBER_PASSWORD},
    )
    assert accepted.status_code == 201
    # The barber role gets a calendar column automatically.
    assert accepted.json()["barber_id"] is not None

    # An invite works exactly once.
    reuse = await client.post(
        "/team/invites/accept",
        headers={"X-Tenant-Slug": slug},
        json={"token": invite_token, "password": "another-password-123"},
    )
    assert reuse.status_code == 400


async def test_barber_cannot_manage_team_or_configure(client, core_key, slug):
    await create_shop(client, core_key, slug, EMAIL, PASSWORD)
    owner = (await login(client, slug, EMAIL, PASSWORD)).json()["access_token"]
    barber = await _invite_barber(client, slug, owner)

    denied = await client.post(
        "/team/invites",
        headers=auth(slug, barber),
        json={"name": "X", "email": "x@y.com", "role": "receptionist"},
    )
    assert denied.status_code == 403
    assert "team:manage" in denied.json()["detail"]

    config = await client.patch("/tenant", headers=auth(slug, barber), json={"name": "Renamed"})
    assert config.status_code == 403


async def test_barber_has_own_scope_on_appointments(client, core_key, slug):
    await create_shop(client, core_key, slug, EMAIL, PASSWORD)
    owner = (await login(client, slug, EMAIL, PASSWORD)).json()["access_token"]
    barber = await _invite_barber(client, slug, owner)

    permissions = (await client.get("/auth/me", headers=auth(slug, barber))).json()["permissions"]

    assert permissions["appointment:read"] == "own"
    assert "finance:read" not in permissions
    assert "appointment:cancel" not in permissions


async def test_owner_cannot_deactivate_self(client, core_key, slug):
    registration = await create_shop(client, core_key, slug, EMAIL, PASSWORD)
    token = (await login(client, slug, EMAIL, PASSWORD)).json()["access_token"]

    resp = await client.delete(f"/team/{registration['user']['id']}", headers=auth(slug, token))
    assert resp.status_code == 400
