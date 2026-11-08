"""Days off, vacation, sick leave and blocks (spec S02)."""

from datetime import UTC, datetime, timedelta

from app.core.database import tenant_session
from app.modules.identity.public import schema_name_for
from app.modules.scheduling.model import BarberTimeOff, TimeOffKind
from tests.conftest import auth, member_token, new_barber, owner_token
from tests.test_scheduling._helpers import main_unit, new_unit, next_weekday


async def _post(client, slug, token, **body):
    return await client.post("/time-off", headers=auth(slug, token), json=body)


async def test_vacation_lifecycle(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    barber = await new_barber(client, slug, owner)
    first = next_weekday(1)
    last = first + timedelta(days=14)
    resp = await _post(
        client,
        slug,
        owner,
        barber_id=barber["id"],
        kind="vacation",
        starts_on=first.isoformat(),
        ends_on=last.isoformat(),
        reason="Férias de verão",
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["affected_appointments"] == []
    vacation = body["time_off"]
    assert (vacation["starts_on"], vacation["ends_on"], vacation["all_day"]) == (
        first.isoformat(),
        last.isoformat(),
        True,
    )
    # Stored from local midnight (São Paulo, UTC−3) to the midnight after the last day (T3).
    assert vacation["starts_at"].startswith(f"{first.isoformat()}T03:00:00")

    overlap = await _post(
        client,
        slug,
        owner,
        barber_id=barber["id"],
        kind="day_off",
        starts_on=last.isoformat(),
        ends_on=last.isoformat(),
    )
    assert overlap.status_code == 409

    query = f"from={first.isoformat()}&to={first.isoformat()}"
    listed = (await client.get(f"/time-off?{query}", headers=auth(slug, owner))).json()
    assert [t["id"] for t in listed] == [vacation["id"]]
    before = (first - timedelta(days=1)).isoformat()
    none = (
        await client.get(f"/time-off?from={before}&to={before}", headers=auth(slug, owner))
    ).json()
    assert none == []

    path = f"/time-off/{vacation['id']}"
    shorter = await client.patch(
        path, headers=auth(slug, owner), json={"ends_on": (first + timedelta(days=6)).isoformat()}
    )
    assert shorter.status_code == 200, shorter.text
    assert shorter.json()["time_off"]["ends_on"] == (first + timedelta(days=6)).isoformat()
    assert shorter.json()["time_off"]["reason"] == "Férias de verão"  # untouched
    assert (await client.delete(path, headers=auth(slug, owner))).status_code == 204


async def test_validation(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    bid = (await new_barber(client, slug, owner))["id"]
    day = next_weekday(2)
    at = lambda h, m=0, d=day: f"{d.isoformat()}T{h:02d}:{m:02d}:00-03:00"  # noqa: E731
    for body in (
        {"kind": "day_off"},  # no dates
        {"kind": "day_off", "starts_at": at(9), "ends_at": at(10)},  # whole day with times
        {
            "kind": "vacation",
            "starts_on": day.isoformat(),
            "ends_on": (day + timedelta(days=180)).isoformat(),
        },
        {"kind": "day_off", "starts_on": "2020-01-01", "ends_on": "2020-01-02"},  # past
        {"kind": "block", "starts_on": day.isoformat(), "ends_on": day.isoformat()},
        {"kind": "block", "starts_at": at(9, 3), "ends_at": at(10)},  # not 5-minute
        {
            "kind": "block",
            "starts_at": at(22),
            "ends_at": at(2, d=day + timedelta(days=1)),
        },  # two days
        {"kind": "block", "starts_at": at(10), "ends_at": at(9)},
    ):
        resp = await _post(client, slug, owner, barber_id=bid, **body)
        assert resp.status_code == 422, (body, resp.text)

    ok = await _post(
        client, slug, owner, barber_id=bid, kind="block", starts_at=at(15), ends_at=at(16)
    )
    assert ok.status_code == 201, ok.text
    assert ok.json()["time_off"]["all_day"] is False


async def test_who_may_do_what(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    centro = await main_unit(client, slug, owner)
    sul = await new_unit(client, slug, owner, "Zona Sul")
    here = await new_barber(client, slug, owner, name="Diego Centro", unit_id=centro)
    there = await new_barber(client, slug, owner, name="Léo Sul", unit_id=sul)
    desk = await member_token(
        client, slug, owner, role="receptionist", email="d@x.com", unit_ids=[centro]
    )
    own = await member_token(
        client, slug, owner, role="barber", email="b@x.com", barber_id=here["id"]
    )
    manager = await member_token(
        client, slug, owner, role="manager", email="m@x.com", unit_ids=[centro]
    )

    day = next_weekday(3)
    block = {
        "kind": "block",
        "starts_at": f"{day}T15:00:00-03:00",
        "ends_at": f"{day}T16:00:00-03:00",
    }
    off = {"kind": "day_off", "starts_on": day.isoformat(), "ends_on": day.isoformat()}

    # Front desk: blocks yes, days off no; only in their unit.
    assert (await _post(client, slug, desk, barber_id=here["id"], **block)).status_code == 201
    assert (await _post(client, slug, desk, barber_id=here["id"], **off)).status_code == 403
    assert (await _post(client, slug, desk, barber_id=there["id"], **block)).status_code == 404
    # The barber blocks only their own column (Q-S02-3).
    later = {**block, "starts_at": f"{day}T17:00:00-03:00", "ends_at": f"{day}T18:00:00-03:00"}
    assert (await _post(client, slug, own, barber_id=here["id"], **later)).status_code == 201
    assert (await _post(client, slug, own, barber_id=there["id"], **later)).status_code == 404
    assert (await _post(client, slug, own, barber_id=here["id"], **off)).status_code == 403
    # Manager: days off in their unit only.
    assert (await _post(client, slug, manager, barber_id=there["id"], **off)).status_code == 404

    mine = (await client.get(f"/time-off?from={day}&to={day}", headers=auth(slug, own))).json()
    assert {t["barber_id"] for t in mine} == {here["id"]}


async def test_past_block_stays_past_day_off_goes(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    bid = (await new_barber(client, slug, owner))["id"]
    yesterday = datetime.now(UTC) - timedelta(days=1)
    async with tenant_session(schema_name_for(slug)) as session:
        block = BarberTimeOff(
            barber_id=bid,
            kind=TimeOffKind.BLOCK,
            all_day=False,
            starts_at=yesterday,
            ends_at=yesterday + timedelta(hours=1),
        )
        off = BarberTimeOff(
            barber_id=bid,
            kind=TimeOffKind.DAY_OFF,
            all_day=True,
            starts_at=yesterday - timedelta(days=3),
            ends_at=yesterday - timedelta(days=2),
        )
        session.add_all([block, off])
        await session.flush()
        block_id, off_id = block.id, off.id

    assert (
        await client.delete(f"/time-off/{block_id}", headers=auth(slug, owner))
    ).status_code == 422
    edit = await client.patch(
        f"/time-off/{off_id}", headers=auth(slug, owner), json={"reason": "x"}
    )
    assert edit.status_code == 422
    assert (
        await client.delete(f"/time-off/{off_id}", headers=auth(slug, owner))
    ).status_code == 204


async def test_shops_do_not_see_each_other(client, core_key, slug):
    owner_a = await owner_token(client, core_key, f"{slug}a")
    owner_b = await owner_token(client, core_key, f"{slug}b")
    bid = (await new_barber(client, f"{slug}a", owner_a))["id"]
    day = next_weekday(4)
    created = await _post(
        client,
        f"{slug}a",
        owner_a,
        barber_id=bid,
        kind="day_off",
        starts_on=day.isoformat(),
        ends_on=day.isoformat(),
    )
    tid = created.json()["time_off"]["id"]
    b = auth(f"{slug}b", owner_b)
    assert (await client.get(f"/time-off?from={day}&to={day}", headers=b)).json() == []
    assert (
        await client.patch(f"/time-off/{tid}", headers=b, json={"reason": "x"})
    ).status_code == 404
    assert (await client.delete(f"/time-off/{tid}", headers=b)).status_code == 404
    assert (
        await _post(
            client,
            f"{slug}b",
            owner_b,
            barber_id=bid,
            kind="day_off",
            starts_on=day.isoformat(),
            ends_on=day.isoformat(),
        )
    ).status_code == 404
