"""Barber registry (spec registry-basic-crud): separate from logins, scoped by unit."""

from tests.conftest import (
    OWNER_EMAIL,
    add_unit,
    auth,
    create_shop,
    login,
    member_token,
    new_barber,
    owner_token,
)


async def _units(client, slug, token) -> list[str]:
    return [u["id"] for u in (await client.get("/tenant/units", headers=auth(slug, token))).json()]


async def test_crud_without_creating_a_login(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    team_before = (await client.get("/team", headers=auth(slug, owner))).json()

    barber = await new_barber(client, slug, owner, name="  Diego   Martins ", default_commission=45)
    assert barber["name"] == "Diego   Martins"
    assert barber["initials"] == "DM"  # derived from the name
    assert barber["default_commission"] == 45
    assert barber["user_id"] is None and barber["email"] is None
    # Registering a barber never creates a login.
    assert (await client.get("/team", headers=auth(slug, owner))).json() == team_before

    path = f"/barbers/{barber['id']}"
    updated = await client.patch(
        path, headers=auth(slug, owner), json={"initials": "dg", "active": False}
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["initials"] == "DG"
    assert updated.json()["name"] == "Diego   Martins"  # untouched
    assert updated.json()["updated_at"] >= barber["updated_at"]

    inactive = await client.get("/barbers?active=false", headers=auth(slug, owner))
    assert [b["id"] for b in inactive.json()] == [barber["id"]]
    assert (await client.get("/barbers?active=true", headers=auth(slug, owner))).json() == []

    assert (await client.delete(path, headers=auth(slug, owner))).status_code == 204
    assert (await client.get(path, headers=auth(slug, owner))).status_code == 404


async def test_validation(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    unit = (await _units(client, slug, owner))[0]
    for body in (
        {"name": "D", "unit_id": unit},
        {"name": "Diego", "unit_id": unit, "default_commission": 101},
        {"name": "Diego"},
    ):
        resp = await client.post("/barbers", headers=auth(slug, owner), json=body)
        assert resp.status_code == 422, body

    unknown_unit = await client.post(
        "/barbers",
        headers=auth(slug, owner),
        json={"name": "Diego", "unit_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert unknown_unit.status_code == 400


async def test_owner_who_also_cuts_is_linked_explicitly(client, core_key, slug):
    shop = await create_shop(client, core_key, slug, OWNER_EMAIL, "owner-password-123")
    owner = (await login(client, slug, OWNER_EMAIL, "owner-password-123")).json()["access_token"]
    owner_id = shop["user"]["id"]

    barber = await new_barber(client, slug, owner, name="Dono", user_id=owner_id)
    assert barber["email"] == OWNER_EMAIL

    # One login, one barber.
    again = await client.post(
        "/barbers",
        headers=auth(slug, owner),
        json={"name": "Outro", "unit_id": barber["unit_id"], "user_id": owner_id},
    )
    assert again.status_code == 409

    # Linked: cannot be deleted, can be unlinked (the owner does not depend on it).
    path = f"/barbers/{barber['id']}"
    assert (await client.delete(path, headers=auth(slug, owner))).status_code == 409
    unlinked = await client.patch(path, headers=auth(slug, owner), json={"user_id": None})
    assert unlinked.status_code == 200
    assert unlinked.json()["email"] is None
    assert (await client.delete(path, headers=auth(slug, owner))).status_code == 204


async def test_barber_role_invite_needs_a_registered_barber(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    no_barber = await client.post(
        "/team/invites",
        headers=auth(slug, owner),
        json={"name": "Diego", "email": "diego@x.com", "role": "barber"},
    )
    assert no_barber.status_code == 422

    unknown = await client.post(
        "/team/invites",
        headers=auth(slug, owner),
        json={
            "name": "Diego",
            "email": "diego@x.com",
            "role": "barber",
            "barber_id": "00000000-0000-0000-0000-000000000000",
        },
    )
    assert unknown.status_code == 400

    barber = await new_barber(client, slug, owner)
    body = {"name": "Diego", "email": "diego@x.com", "role": "barber", "barber_id": barber["id"]}
    first = await client.post("/team/invites", headers=auth(slug, owner), json=body)
    assert first.status_code == 201
    # A second pending invite for the same barber is refused.
    second = await client.post(
        "/team/invites", headers=auth(slug, owner), json={**body, "email": "other@x.com"}
    )
    assert second.status_code == 409


async def test_linked_barber_login(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    barber = await new_barber(client, slug, owner)
    token = await member_token(
        client, slug, owner, role="barber", email="diego@x.com", barber_id=barber["id"]
    )

    me = (await client.get("/auth/me", headers=auth(slug, token))).json()
    assert me["barber_id"] == barber["id"]

    path = f"/barbers/{barber['id']}"
    # Already has access: no new invite, and a barber login cannot lose its barber.
    reinvite = await client.post(
        "/team/invites",
        headers=auth(slug, owner),
        json={"name": "Diego", "email": "d2@x.com", "role": "barber", "barber_id": barber["id"]},
    )
    assert reinvite.status_code == 409
    unlink = await client.patch(path, headers=auth(slug, owner), json={"user_id": None})
    assert unlink.status_code == 409
    assert (await client.delete(path, headers=auth(slug, owner))).status_code == 409
    # Inactivating is fine.
    inactive = await client.patch(path, headers=auth(slug, owner), json={"active": False})
    assert inactive.status_code == 200


async def test_accepting_an_invite_never_creates_a_barber(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    await member_token(client, slug, owner, role="receptionist", email="desk@x.com")
    assert (await client.get("/barbers", headers=auth(slug, owner))).json() == []


async def test_unit_scope(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    centro = (await _units(client, slug, owner))[0]
    sul = await add_unit(slug, "Zona Sul")
    in_centro = await new_barber(client, slug, owner, name="Centro Barber", unit_id=centro)
    in_sul = await new_barber(client, slug, owner, name="Sul Barber", unit_id=sul)

    manager = await member_token(
        client, slug, owner, role="manager", email="mgr@x.com", unit_ids=[centro]
    )
    listed = (await client.get("/barbers", headers=auth(slug, manager))).json()
    assert [b["id"] for b in listed] == [in_centro["id"]]

    other = f"/barbers/{in_sul['id']}"
    assert (await client.get(other, headers=auth(slug, manager))).status_code == 404
    assert (
        await client.patch(other, headers=auth(slug, manager), json={"name": "X Y"})
    ).status_code == 404
    elsewhere = await client.post(
        "/barbers", headers=auth(slug, manager), json={"name": "Novo", "unit_id": sul}
    )
    assert elsewhere.status_code == 403
    move_out = await client.patch(
        f"/barbers/{in_centro['id']}", headers=auth(slug, manager), json={"unit_id": sul}
    )
    assert move_out.status_code == 403

    # The owner sees every unit.
    assert len((await client.get("/barbers", headers=auth(slug, owner))).json()) == 2


async def test_roles(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    unit = (await _units(client, slug, owner))[0]
    barber = await new_barber(client, slug, owner)
    desk = await member_token(client, slug, owner, role="receptionist", email="desk@x.com")

    assert (await client.get("/barbers", headers=auth(slug, desk))).status_code == 200
    create = await client.post(
        "/barbers", headers=auth(slug, desk), json={"name": "Novo", "unit_id": unit}
    )
    assert create.status_code == 403

    own = await member_token(
        client, slug, owner, role="barber", email="diego@x.com", barber_id=barber["id"]
    )
    # The barber role has no team permissions.
    assert (await client.get("/barbers", headers=auth(slug, own))).status_code == 403


async def test_shops_do_not_see_each_other(client, core_key, slug):
    slug_a, slug_b = f"{slug}a", f"{slug}b"
    owner_a = await owner_token(client, core_key, slug_a)
    owner_b = await owner_token(client, core_key, slug_b)
    barber = await new_barber(client, slug_a, owner_a)

    assert (await client.get("/barbers", headers=auth(slug_b, owner_b))).json() == []
    path = f"/barbers/{barber['id']}"
    assert (await client.get(path, headers=auth(slug_b, owner_b))).status_code == 404
    patch = await client.patch(path, headers=auth(slug_b, owner_b), json={"name": "Hacked"})
    assert patch.status_code == 404
    assert (await client.delete(path, headers=auth(slug_b, owner_b))).status_code == 404
    assert (await client.get(path, headers=auth(slug_a, owner_a))).json()["name"] == barber["name"]
