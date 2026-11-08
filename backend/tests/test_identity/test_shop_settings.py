"""Shop settings: one row per shop, defaults, partial update, who may change it (spec S01)."""

from tests.conftest import auth, member_token, new_barber, owner_token

DEFAULTS = {
    "min_advance_minutes": 60,
    "max_advance_days": 30,
    "confirmation_deadline_hours": 3,
    "client_change_min_hours": 2,
    "late_tolerance_minutes": 10,
    "max_future_appointments_per_client": 3,
    "barber_sees_client_contact": False,
}


async def test_defaults_and_update(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    current = (await client.get("/tenant/settings", headers=auth(slug, owner))).json()
    assert {k: current[k] for k in DEFAULTS} == DEFAULTS
    assert current["contact_phone"] is None

    resp = await client.patch(
        "/tenant/settings",
        headers=auth(slug, owner),
        json={
            "contact_phone": "(11) 98765-4321",
            "instagram": "@barbearia.central",
            "about": "  Desde 1998.  ",
            "min_advance_minutes": 30,
            "max_advance_days": None,  # null on a policy: no change
            "barber_sees_client_contact": True,
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["contact_phone"] == "+5511987654321"
    assert body["instagram"] == "barbearia.central"
    assert body["about"] == "Desde 1998."
    assert body["min_advance_minutes"] == 30
    assert body["max_advance_days"] == 30
    assert body["barber_sees_client_contact"] is True

    cleared = await client.patch(
        "/tenant/settings", headers=auth(slug, owner), json={"about": None}
    )
    assert cleared.json()["about"] is None


async def test_validation(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    for body in (
        {"min_advance_minutes": 50},  # not a multiple of 15
        {"max_advance_days": 0},
        {"confirmation_deadline_hours": 49},
        {"max_future_appointments_per_client": 21},
        {"instagram": "minha barbearia"},
        {"contact_phone": "123"},
    ):
        resp = await client.patch("/tenant/settings", headers=auth(slug, owner), json=body)
        assert resp.status_code == 422, body


async def test_who_reads_and_who_changes(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    barber = await new_barber(client, slug, owner)
    own = await member_token(
        client, slug, owner, role="barber", email="b@x.com", barber_id=barber["id"]
    )
    manager = await member_token(client, slug, owner, role="manager", email="mgr@x.com")

    assert (await client.get("/tenant/settings", headers=auth(slug, own))).status_code == 200
    for token in (own, manager):
        resp = await client.patch(
            "/tenant/settings", headers=auth(slug, token), json={"about": "x"}
        )
        assert resp.status_code == 403
