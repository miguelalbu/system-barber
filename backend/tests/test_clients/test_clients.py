"""Clients (spec registry-basic-crud): E.164 phone, paged search, scopes, isolation."""

import pytest

from app.core.phone import InvalidPhone, normalize_phone
from tests.conftest import auth, member_token, new_barber, owner_token

JOAO = {"name": "João Silva", "phone": "(11) 98765-4321"}


async def _create(client, slug, token, **body):
    resp = await client.post("/clients", headers=auth(slug, token), json={**JOAO, **body})
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.mark.parametrize(
    ("raw", "e164"),
    [
        ("(11) 98765-4321", "+5511987654321"),
        ("11 3333-4444", "+551133334444"),
        ("+55 11 98765-4321", "+5511987654321"),
        ("5511987654321", "+5511987654321"),
        ("+1 415 555 2671", "+14155552671"),
    ],
)
def test_phone_normalization(raw, e164):
    assert normalize_phone(raw) == e164


@pytest.mark.parametrize("raw", ["", "1234", "98765-4321", "+12", "abc"])
def test_invalid_phone(raw):
    with pytest.raises(InvalidPhone):
        normalize_phone(raw)


async def test_crud(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    created = await _create(
        client, slug, owner, email="Joao@Mail.COM", birth_date="1990-05-17", notes=""
    )
    assert created["phone"] == "+5511987654321"
    assert created["email"] == "joao@mail.com"
    assert created["notes"] is None

    path = f"/clients/{created['id']}"
    updated = await client.patch(
        path,
        headers=auth(slug, owner),
        json={"email": None, "name": None, "notes": "Prefere tarde"},
    )
    assert updated.status_code == 200, updated.text
    body = updated.json()
    assert body["email"] is None  # optional field cleared
    assert body["name"] == "João Silva"  # null on a required field: no change
    assert body["notes"] == "Prefere tarde"

    assert (await client.delete(path, headers=auth(slug, owner))).status_code == 204
    assert (await client.get(path, headers=auth(slug, owner))).status_code == 404


async def test_phone_is_unique_whatever_the_format(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    await _create(client, slug, owner)
    dup = await client.post(
        "/clients",
        headers=auth(slug, owner),
        json={"name": "Outro", "phone": "+55 11 98765 4321"},
    )
    assert dup.status_code == 409
    assert "telefone" in dup.json()["detail"]

    other = await _create(client, slug, owner, name="Maria", phone="11912345678")
    taken = await client.patch(
        f"/clients/{other['id']}", headers=auth(slug, owner), json={"phone": "11987654321"}
    )
    assert taken.status_code == 409


async def test_validation(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    for bad in (
        {"phone": "1234"},
        {"phone": None},
        {"name": "J"},
        {"email": "not-an-email"},
        {"birth_date": "2999-01-01"},
    ):
        resp = await client.post("/clients", headers=auth(slug, owner), json={**JOAO, **bad})
        assert resp.status_code == 422, bad


async def test_search_and_pages(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    await _create(client, slug, owner, name="Ana Souza", phone="11900000001")
    await _create(client, slug, owner, name="bruno lima", phone="11900000002")
    await _create(client, slug, owner, name="Carla Souza", phone="21900000003", active=False)

    page = (await client.get("/clients?limit=2", headers=auth(slug, owner))).json()
    assert page["total"] == 3
    assert [c["name"] for c in page["items"]] == ["Ana Souza", "bruno lima"]
    rest = (await client.get("/clients?limit=2&offset=2", headers=auth(slug, owner))).json()
    assert [c["name"] for c in rest["items"]] == ["Carla Souza"]

    by_name = (await client.get("/clients?q=souza", headers=auth(slug, owner))).json()
    assert by_name["total"] == 2
    by_phone = (await client.get("/clients?q=(21) 9", headers=auth(slug, owner))).json()
    assert [c["name"] for c in by_phone["items"]] == ["Carla Souza"]
    # Wildcards typed by the user are literal.
    assert (await client.get("/clients?q=%25", headers=auth(slug, owner))).json()["total"] == 0
    active = (await client.get("/clients?active=true", headers=auth(slug, owner))).json()
    assert active["total"] == 2

    too_big = await client.get("/clients?limit=101", headers=auth(slug, owner))
    assert too_big.status_code == 422


async def test_roles(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    joao = await _create(client, slug, owner)

    desk = await member_token(client, slug, owner, role="receptionist", email="desk@x.com")
    assert (
        await client.post(
            "/clients", headers=auth(slug, desk), json={"name": "Maria", "phone": "11912345678"}
        )
    ).status_code == 201

    barber = await new_barber(client, slug, owner)
    own = await member_token(
        client, slug, owner, role="barber", email="diego@x.com", barber_id=barber["id"]
    )
    # `own`: only the clients they served — none until scheduling exists.
    listed = (await client.get("/clients", headers=auth(slug, own))).json()
    assert listed == {"items": [], "total": 0}
    assert (await client.get(f"/clients/{joao['id']}", headers=auth(slug, own))).status_code == 404
    write = await client.post("/clients", headers=auth(slug, own), json=JOAO)
    assert write.status_code == 403


async def test_shops_do_not_see_each_other(client, core_key, slug):
    slug_a, slug_b = f"{slug}a", f"{slug}b"
    owner_a = await owner_token(client, core_key, slug_a)
    owner_b = await owner_token(client, core_key, slug_b)
    joao = await _create(client, slug_a, owner_a)

    assert (await client.get("/clients", headers=auth(slug_b, owner_b))).json()["total"] == 0
    path = f"/clients/{joao['id']}"
    assert (await client.get(path, headers=auth(slug_b, owner_b))).status_code == 404
    assert (
        await client.patch(path, headers=auth(slug_b, owner_b), json={"name": "Hacked"})
    ).status_code == 404
    assert (await client.delete(path, headers=auth(slug_b, owner_b))).status_code == 404
    # The same phone is free in another shop.
    await _create(client, slug_b, owner_b)
    assert (await client.get(path, headers=auth(slug_a, owner_a))).json()["name"] == "João Silva"
