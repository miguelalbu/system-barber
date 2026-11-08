"""Units: CRUD, the rules that keep a shop servable, scope and isolation (spec S01)."""

from tests.conftest import auth, member_token, new_barber, owner_token


async def _units(client, slug, token, query: str = "") -> list[dict]:
    return (await client.get(f"/tenant/units{query}", headers=auth(slug, token))).json()


async def _create(client, slug, token, **body) -> dict:
    resp = await client.post(
        "/tenant/units", headers=auth(slug, token), json={"name": "Zona Sul", **body}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_crud(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    unit = await _create(
        client, slug, owner, phone="(11) 3333-4444", address="  Rua A, 10 ", online_booking=False
    )
    assert unit["phone"] == "+551133334444"
    assert unit["address"] == "Rua A, 10"
    assert unit["timezone"] == "America/Sao_Paulo"
    assert unit["online_booking"] is False

    # Born open Monday to Saturday, 09:00–19:00 (T6).
    hours = (
        await client.get(f"/tenant/units/{unit['id']}/hours", headers=auth(slug, owner))
    ).json()
    assert [len(d["intervals"]) for d in hours["days"]] == [1, 1, 1, 1, 1, 1, 0]
    assert hours["days"][0]["intervals"] == [{"opens_at": "09:00", "closes_at": "19:00"}]

    path = f"/tenant/units/{unit['id']}"
    assert (await client.get(path, headers=auth(slug, owner))).json()["name"] == "Zona Sul"
    patched = await client.patch(
        path, headers=auth(slug, owner), json={"address": None, "timezone": None, "name": "Sul"}
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["address"] is None  # null clears
    assert patched.json()["timezone"] == "America/Sao_Paulo"  # null on a required field: no change
    assert patched.json()["name"] == "Sul"

    duplicate = await client.post("/tenant/units", headers=auth(slug, owner), json={"name": "SUL"})
    assert duplicate.status_code == 409

    await client.patch(path, headers=auth(slug, owner), json={"active": False})
    assert [u["name"] for u in await _units(client, slug, owner, "?active=false")] == ["Sul"]
    assert "Sul" not in [u["name"] for u in await _units(client, slug, owner, "?active=true")]

    assert (await client.delete(path, headers=auth(slug, owner))).status_code == 204
    assert (await client.get(path, headers=auth(slug, owner))).status_code == 404


async def test_validation(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    for body in (
        {"name": "X"},
        {"name": "Sul", "timezone": "Mars/Base"},
        {"name": "Sul", "phone": "12"},
    ):
        resp = await client.post("/tenant/units", headers=auth(slug, owner), json=body)
        assert resp.status_code == 422, body


async def test_the_shop_keeps_one_active_unit(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    (main,) = await _units(client, slug, owner)
    path = f"/tenant/units/{main['id']}"
    inactive = await client.patch(path, headers=auth(slug, owner), json={"active": False})
    assert inactive.status_code == 409
    assert "pelo menos uma unidade ativa" in inactive.json()["detail"]
    assert (await client.delete(path, headers=auth(slug, owner))).status_code == 409


async def test_unit_with_barbers_or_users(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    sul = await _create(client, slug, owner)
    path = f"/tenant/units/{sul['id']}"
    barber = await new_barber(client, slug, owner, unit_id=sul["id"])

    # Active barbers block inactivating; any barber is history and blocks deleting.
    blocked = await client.patch(path, headers=auth(slug, owner), json={"active": False})
    assert blocked.status_code == 409
    assert "barbeiros" in blocked.json()["detail"]
    await client.patch(
        f"/barbers/{barber['id']}", headers=auth(slug, owner), json={"active": False}
    )
    assert (
        await client.patch(path, headers=auth(slug, owner), json={"active": False})
    ).status_code == 200
    history = await client.delete(path, headers=auth(slug, owner))
    assert history.status_code == 409
    assert "histórico" in history.json()["detail"]

    # A unit a user is restricted to cannot vanish (they would see every unit).
    norte = await _create(client, slug, owner, name="Norte")
    await member_token(
        client, slug, owner, role="receptionist", email="desk@x.com", unit_ids=[norte["id"]]
    )
    linked = await client.delete(f"/tenant/units/{norte['id']}", headers=auth(slug, owner))
    assert linked.status_code == 409
    assert "Equipe" in linked.json()["detail"]


async def test_roles_and_scope(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    (main,) = await _units(client, slug, owner)
    sul = await _create(client, slug, owner)
    manager = await member_token(
        client, slug, owner, role="manager", email="mgr@x.com", unit_ids=[main["id"]]
    )

    assert [u["id"] for u in await _units(client, slug, manager)] == [main["id"]]
    assert (
        await client.get(f"/tenant/units/{sul['id']}", headers=auth(slug, manager))
    ).status_code == 404
    # Units themselves are the owner's (tenant:configure).
    for method, path, body in (
        ("post", "/tenant/units", {"name": "Leste"}),
        ("patch", f"/tenant/units/{main['id']}", {"name": "Outro"}),
        ("delete", f"/tenant/units/{sul['id']}", None),
    ):
        kwargs = {"json": body} if body is not None else {}
        resp = await getattr(client, method)(path, headers=auth(slug, manager), **kwargs)
        assert resp.status_code == 403, (method, path)


async def test_auth_me_still_lists_units(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    me = (await client.get("/auth/me", headers=auth(slug, owner))).json()
    assert len(me["units"]) == 1
    assert me["units"][0]["online_booking"] is True


async def test_shops_do_not_see_each_other(client, core_key, slug):
    slug_a, slug_b = f"{slug}a", f"{slug}b"
    owner_a = await owner_token(client, core_key, slug_a)
    owner_b = await owner_token(client, core_key, slug_b)
    unit = await _create(client, slug_a, owner_a)
    exception = await client.post(
        "/tenant/unit-exceptions",
        headers=auth(slug_a, owner_a),
        json={
            "unit_ids": [unit["id"]],
            "starts_on": "2099-12-24",
            "ends_on": "2099-12-25",
            "kind": "closed",
        },
    )
    assert exception.status_code == 201, exception.text
    exception_id = exception.json()[0]["id"]
    await client.patch("/tenant/settings", headers=auth(slug_a, owner_a), json={"about": "Loja A"})

    b = auth(slug_b, owner_b)
    path = f"/tenant/units/{unit['id']}"
    assert unit["id"] not in [u["id"] for u in await _units(client, slug_b, owner_b)]
    assert (await client.get(path, headers=b)).status_code == 404
    assert (await client.patch(path, headers=b, json={"name": "Hacked"})).status_code == 404
    assert (await client.delete(path, headers=b)).status_code == 404
    week = {"days": [{"weekday": d, "intervals": []} for d in range(1, 8)]}
    assert (await client.put(f"{path}/hours", headers=b, json=week)).status_code == 404
    assert (await client.get("/tenant/unit-exceptions", headers=b)).json() == []
    ex_path = f"/tenant/unit-exceptions/{exception_id}"
    assert (await client.patch(ex_path, headers=b, json={"reason": "x"})).status_code == 404
    assert (await client.delete(ex_path, headers=b)).status_code == 404
    assert (await client.get("/tenant/settings", headers=b)).json()["about"] is None
    # A is intact.
    assert (await client.get(path, headers=auth(slug_a, owner_a))).json()["name"] == "Zona Sul"
