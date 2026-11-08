"""Weekly schedule and special shifts (spec S02)."""

from tests.conftest import auth, member_token, new_barber, owner_token
from tests.test_scheduling._helpers import main_unit, new_unit, next_weekday, week


async def test_without_schedule_follows_the_unit(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    barber = await new_barber(client, slug, owner)
    body = (await client.get(f"/barbers/{barber['id']}/schedule", headers=auth(slug, owner))).json()
    assert body["configured"] is False
    assert body["days"][0]["intervals"] == [{"starts_at": "09:00", "ends_at": "19:00"}]
    assert body["days"][6]["intervals"] == []  # Sunday: the unit is closed
    assert body["weekly_minutes"] == 6 * 600
    assert body["warnings"] == []


async def test_replace_the_week(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    barber = await new_barber(client, slug, owner)
    path = f"/barbers/{barber['id']}/schedule"
    lunch = [("13:00", "20:00"), ("09:00", "12:00")]  # out of order; ends after the unit closes
    resp = await client.put(
        path, headers=auth(slug, owner), json=week(d1=lunch, d2=[("10:00", "16:00")])
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["configured"] is True
    assert body["days"][0]["intervals"] == [
        {"starts_at": "09:00", "ends_at": "12:00"},
        {"starts_at": "13:00", "ends_at": "20:00"},
    ]
    # Effective = schedule ∩ unit: Monday 3 h + 6 h (not 7 h), Tuesday 6 h.
    assert body["weekly_minutes"] == (180 + 360) + 360
    assert body["warnings"] == ["Segunda 19:00–20:00 fica fora do horário da unidade"]
    assert (await client.get(path, headers=auth(slug, owner))).json() == body


async def test_validation(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    path = f"/barbers/{(await new_barber(client, slug, owner))['id']}/schedule"
    empty = await client.put(path, headers=auth(slug, owner), json=week())
    assert empty.status_code == 422
    assert "registre uma ausência ou inative" in empty.json()["detail"]
    for body in (
        week(d1=[("09:00", "12:00"), ("12:00", "13:00")]),  # touching
        week(d1=[("09:00", "12:00"), ("11:00", "13:00")]),  # overlapping
        week(d1=[("09:02", "12:00")]),
        week(d1=[("12:00", "09:00")]),
    ):
        assert (await client.put(path, headers=auth(slug, owner), json=body)).status_code == 422


async def test_special_shift(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    barber = await new_barber(client, slug, owner)
    day = next_weekday(6)  # a Saturday
    path = f"/barbers/{barber['id']}/shift-overrides/{day.isoformat()}"
    resp = await client.put(
        path,
        headers=auth(slug, owner),
        json={"intervals": [{"starts_at": "14:00", "ends_at": "20:00"}], "reason": "Só à tarde"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["warnings"] == [f"{day:%d/%m} 19:00–20:00 fica fora do horário da unidade"]

    listed = (
        await client.get(f"/barbers/{barber['id']}/shift-overrides", headers=auth(slug, owner))
    ).json()
    assert [(o["date"], o["reason"]) for o in listed] == [(day.isoformat(), "Só à tarde")]

    assert (await client.delete(path, headers=auth(slug, owner))).status_code == 204
    assert (await client.delete(path, headers=auth(slug, owner))).status_code == 404
    past = f"/barbers/{barber['id']}/shift-overrides/2020-01-04"
    body = {"intervals": [{"starts_at": "09:00", "ends_at": "12:00"}]}
    assert (await client.put(past, headers=auth(slug, owner), json=body)).status_code == 422


async def test_scopes(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    centro = await main_unit(client, slug, owner)
    sul = await new_unit(client, slug, owner, "Zona Sul")
    here = await new_barber(client, slug, owner, name="Diego Centro", unit_id=centro)
    there = await new_barber(client, slug, owner, name="Léo Sul", unit_id=sul)
    manager = await member_token(
        client, slug, owner, role="manager", email="m@x.com", unit_ids=[centro]
    )
    desk = await member_token(
        client, slug, owner, role="receptionist", email="d@x.com", unit_ids=[centro]
    )
    own = await member_token(
        client, slug, owner, role="barber", email="b@x.com", barber_id=here["id"]
    )

    body = week(d1=[("10:00", "18:00")])
    assert (
        await client.put(f"/barbers/{here['id']}/schedule", headers=auth(slug, manager), json=body)
    ).status_code == 200
    assert (
        await client.put(f"/barbers/{there['id']}/schedule", headers=auth(slug, manager), json=body)
    ).status_code == 404
    assert (
        await client.put(f"/barbers/{here['id']}/schedule", headers=auth(slug, desk), json=body)
    ).status_code == 403
    assert (
        await client.get(f"/barbers/{here['id']}/schedule", headers=auth(slug, desk))
    ).status_code == 200
    assert (
        await client.get(f"/barbers/{there['id']}/schedule", headers=auth(slug, desk))
    ).status_code == 404

    # The barber reads only their own schedule.
    assert (
        await client.get(f"/barbers/{here['id']}/schedule", headers=auth(slug, own))
    ).status_code == 200
    assert (
        await client.get(f"/barbers/{there['id']}/schedule", headers=auth(slug, own))
    ).status_code == 404
    grid = (await client.get("/schedules", headers=auth(slug, own))).json()
    assert [r["barber_id"] for r in grid] == [here["id"]]
    assert len((await client.get("/schedules", headers=auth(slug, owner))).json()) == 2
    only_sul = (await client.get(f"/schedules?unit_id={sul}", headers=auth(slug, owner))).json()
    assert [r["barber_id"] for r in only_sul] == [there["id"]]


async def test_shops_do_not_see_each_other(client, core_key, slug):
    owner_a = await owner_token(client, core_key, f"{slug}a")
    owner_b = await owner_token(client, core_key, f"{slug}b")
    barber = await new_barber(client, f"{slug}a", owner_a)
    b = auth(f"{slug}b", owner_b)
    path = f"/barbers/{barber['id']}/schedule"
    assert (await client.get(path, headers=b)).status_code == 404
    assert (
        await client.put(path, headers=b, json=week(d1=[("09:00", "10:00")]))
    ).status_code == 404
    assert (await client.get("/schedules", headers=b)).json() == []
