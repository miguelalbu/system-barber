"""Services and barber ↔ service links (spec registry-basic-crud)."""

from tests.conftest import auth, member_token, new_barber, owner_token

CORTE = {"name": "Corte", "duration_minutes": 30, "price_cents": 4500}


async def _create(client, slug, token, **body):
    resp = await client.post("/services", headers=auth(slug, token), json={**CORTE, **body})
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_crud(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    service = await _create(client, slug, owner, description="  ")
    assert service["description"] is None  # blank is no description
    assert service["active"] is True
    assert service["barber_ids"] == []

    path = f"/services/{service['id']}"
    updated = await client.patch(
        path, headers=auth(slug, owner), json={"price_cents": 5000, "description": "Na tesoura"}
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["price_cents"] == 5000
    assert updated.json()["duration_minutes"] == 30  # untouched
    cleared = await client.patch(path, headers=auth(slug, owner), json={"description": None})
    assert cleared.json()["description"] is None

    await _create(client, slug, owner, name="barba", active=False)
    names = [s["name"] for s in (await client.get("/services", headers=auth(slug, owner))).json()]
    assert names == ["barba", "Corte"]  # by name, case-insensitive
    active = (await client.get("/services?active=true", headers=auth(slug, owner))).json()
    assert [s["name"] for s in active] == ["Corte"]

    assert (await client.delete(path, headers=auth(slug, owner))).status_code == 204
    assert (await client.get(path, headers=auth(slug, owner))).status_code == 404


async def test_name_is_unique_case_insensitive(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    await _create(client, slug, owner)
    dup = await client.post(
        "/services", headers=auth(slug, owner), json={**CORTE, "name": " CORTE "}
    )
    assert dup.status_code == 409

    barba = await _create(client, slug, owner, name="Barba")
    rename = await client.patch(
        f"/services/{barba['id']}", headers=auth(slug, owner), json={"name": "corte"}
    )
    assert rename.status_code == 409


async def test_validation(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    for bad in (
        {"duration_minutes": 32},
        {"duration_minutes": 0},
        {"duration_minutes": 485},
        {"price_cents": -1},
        {"name": "C"},
    ):
        resp = await client.post("/services", headers=auth(slug, owner), json={**CORTE, **bad})
        assert resp.status_code == 422, bad


async def test_write_needs_every_unit(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    unit = (await client.get("/tenant/units", headers=auth(slug, owner))).json()[0]["id"]
    restricted = await member_token(
        client, slug, owner, role="manager", email="mgr@x.com", unit_ids=[unit]
    )
    resp = await client.post("/services", headers=auth(slug, restricted), json=CORTE)
    assert resp.status_code == 403
    assert "todas as unidades" in resp.json()["detail"]

    everywhere = await member_token(client, slug, owner, role="manager", email="all@x.com")
    assert (
        await client.post("/services", headers=auth(slug, everywhere), json=CORTE)
    ).status_code == 201


async def test_roles(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    service = await _create(client, slug, owner)
    desk = await member_token(client, slug, owner, role="receptionist", email="desk@x.com")
    barber = await new_barber(client, slug, owner)
    own = await member_token(
        client, slug, owner, role="barber", email="diego@x.com", barber_id=barber["id"]
    )

    for token in (desk, own):
        assert (await client.get("/services", headers=auth(slug, token))).status_code == 200
        write = await client.patch(
            f"/services/{service['id']}", headers=auth(slug, token), json={"price_cents": 1}
        )
        assert write.status_code == 403


async def test_barber_services(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    corte = await _create(client, slug, owner)
    barba = await _create(client, slug, owner, name="Barba", active=False)
    barber = await new_barber(client, slug, owner)
    path = f"/barbers/{barber['id']}/services"

    enabled = await client.put(
        path, headers=auth(slug, owner), json={"service_ids": [corte["id"], barba["id"]]}
    )
    assert enabled.status_code == 200, enabled.text
    assert {s["id"] for s in enabled.json()} == {corte["id"], barba["id"]}  # inactive may stay
    listed = (await client.get("/services", headers=auth(slug, owner))).json()
    assert all(s["barber_ids"] == [barber["id"]] for s in listed)

    # Replaces the whole set.
    only = await client.put(path, headers=auth(slug, owner), json={"service_ids": [barba["id"]]})
    assert [s["id"] for s in only.json()] == [barba["id"]]
    corte_now = (await client.get(f"/services/{corte['id']}", headers=auth(slug, owner))).json()
    assert corte_now["barber_ids"] == []

    unknown = await client.put(
        path,
        headers=auth(slug, owner),
        json={"service_ids": ["00000000-0000-0000-0000-000000000000"]},
    )
    assert unknown.status_code == 400

    missing = await client.put(
        "/barbers/00000000-0000-0000-0000-000000000000/services",
        headers=auth(slug, owner),
        json={"service_ids": []},
    )
    assert missing.status_code == 404

    # Links are not history: deleting either side drops them.
    assert (
        await client.delete(f"/barbers/{barber['id']}", headers=auth(slug, owner))
    ).status_code == 204
    barba_now = (await client.get(f"/services/{barba['id']}", headers=auth(slug, owner))).json()
    assert barba_now["barber_ids"] == []


async def test_shops_do_not_see_each_other(client, core_key, slug):
    slug_a, slug_b = f"{slug}a", f"{slug}b"
    owner_a = await owner_token(client, core_key, slug_a)
    owner_b = await owner_token(client, core_key, slug_b)
    service = await _create(client, slug_a, owner_a)
    barber_a = await new_barber(client, slug_a, owner_a)

    assert (await client.get("/services", headers=auth(slug_b, owner_b))).json() == []
    path = f"/services/{service['id']}"
    assert (await client.get(path, headers=auth(slug_b, owner_b))).status_code == 404
    assert (
        await client.patch(path, headers=auth(slug_b, owner_b), json={"price_cents": 1})
    ).status_code == 404
    assert (await client.delete(path, headers=auth(slug_b, owner_b))).status_code == 404
    # B can create a service with A's name: names are unique per shop.
    await _create(client, slug_b, owner_b)
    # A's barber does not exist in B, and A's service cannot be linked from B.
    link = await client.put(
        f"/barbers/{barber_a['id']}/services",
        headers=auth(slug_b, owner_b),
        json={"service_ids": [service["id"]]},
    )
    assert link.status_code == 404
    assert (await client.get(path, headers=auth(slug_a, owner_a))).json()["price_cents"] == 4500
