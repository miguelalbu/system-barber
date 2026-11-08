"""Effective working time: schedule ∩ unit hours − time off (spec S02)."""

from datetime import timedelta

from tests.conftest import auth, new_barber, owner_token
from tests.test_scheduling._helpers import main_unit, new_unit, next_weekday, week


def _day(body: dict, barber_id: str, day) -> dict:
    row = next(b for b in body["barbers"] if b["barber_id"] == barber_id)
    return next(d for d in row["days"] if d["date"] == day.isoformat())


def _spans(day: dict) -> list[tuple[str, str]]:
    return [(i["starts_at"][11:16], i["ends_at"][11:16]) for i in day["intervals"]]


async def test_the_formula(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    unit = await main_unit(client, slug, owner)
    worker = await new_barber(client, slug, owner, name="Diego Martins")
    newbie = await new_barber(client, slug, owner, name="Kaio Novo")
    await client.put(
        f"/barbers/{worker['id']}/schedule",
        headers=auth(slug, owner),
        json=week(
            d1=[("10:00", "12:00"), ("13:00", "20:00")],
            d2=[("09:00", "19:00")],
            d3=[("09:00", "19:00")],
            d4=[("09:00", "19:00")],
        ),
    )
    monday = next_weekday(1)
    tuesday, wednesday, thursday = (monday + timedelta(days=n) for n in (1, 2, 3))
    friday = monday + timedelta(days=4)
    # Tuesday: special shift. Wednesday: a block in the middle. Thursday: day off.
    await client.put(
        f"/barbers/{worker['id']}/shift-overrides/{tuesday}",
        headers=auth(slug, owner),
        json={"intervals": [{"starts_at": "14:00", "ends_at": "18:00"}]},
    )
    await client.post(
        "/time-off",
        headers=auth(slug, owner),
        json={
            "barber_id": worker["id"],
            "kind": "block",
            "starts_at": f"{wednesday}T12:00:00-03:00",
            "ends_at": f"{wednesday}T13:30:00-03:00",
        },
    )
    await client.post(
        "/time-off",
        headers=auth(slug, owner),
        json={
            "barber_id": worker["id"],
            "kind": "day_off",
            "starts_on": thursday.isoformat(),
            "ends_on": thursday.isoformat(),
        },
    )
    # Friday: the whole unit is closed.
    await client.post(
        "/tenant/unit-exceptions",
        headers=auth(slug, owner),
        json={
            "unit_ids": [unit],
            "starts_on": friday.isoformat(),
            "ends_on": friday.isoformat(),
            "kind": "closed",
        },
    )

    resp = await client.get(
        f"/working-time?unit_id={unit}&from={monday}&to={friday}", headers=auth(slug, owner)
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["timezone"] == "America/Sao_Paulo"
    # UTC = local + 3 h. Monday is cut at 19:00 local by the unit.
    assert _spans(_day(body, worker["id"], monday)) == [("13:00", "15:00"), ("16:00", "22:00")]
    assert _day(body, worker["id"], monday)["source"] == "weekly"
    assert _spans(_day(body, worker["id"], tuesday)) == [("17:00", "21:00")]
    assert _day(body, worker["id"], tuesday)["source"] == "override"
    assert _spans(_day(body, worker["id"], wednesday)) == [("12:00", "15:00"), ("16:30", "22:00")]
    thursday_body = _day(body, worker["id"], thursday)
    assert thursday_body["intervals"] == [] and thursday_body["time_off"][0]["kind"] == "day_off"
    assert _day(body, worker["id"], friday)["intervals"] == []
    # No schedule: the unit's hours (T2).
    assert _spans(_day(body, newbie["id"], monday)) == [("12:00", "22:00")]
    assert _day(body, newbie["id"], monday)["source"] == "unit_default"

    too_long = await client.get(
        f"/working-time?unit_id={unit}&from={monday}&to={monday + timedelta(days=40)}",
        headers=auth(slug, owner),
    )
    assert too_long.status_code == 422


async def test_vacation_across_months_and_other_timezone(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    ny = await new_unit(client, slug, owner, "NY", timezone="America/New_York")
    barber = await new_barber(client, slug, owner, unit_id=ny)
    # Around the US switch to daylight time next year (second Sunday of March).
    from datetime import date

    year = date.today().year + 1
    march = date(year, 3, 1)
    switch = march + timedelta(days=(6 - march.weekday()) % 7 + 7)
    friday, monday = switch - timedelta(days=2), switch + timedelta(days=1)
    body = (
        await client.get(
            f"/working-time?unit_id={ny}&from={friday}&to={monday}", headers=auth(slug, owner)
        )
    ).json()
    assert body["timezone"] == "America/New_York"
    assert _spans(_day(body, barber["id"], friday)) == [("14:00", "00:00")]  # EST, UTC−5
    assert _spans(_day(body, barber["id"], monday)) == [("13:00", "23:00")]  # EDT, UTC−4

    # Vacation from the last days of a month into the next.
    end_of_month = date(year, 4, 28)
    await client.post(
        "/time-off",
        headers=auth(slug, owner),
        json={
            "barber_id": barber["id"],
            "kind": "vacation",
            "starts_on": end_of_month.isoformat(),
            "ends_on": (end_of_month + timedelta(days=6)).isoformat(),
        },
    )
    span = (
        await client.get(
            f"/working-time?unit_id={ny}&from={end_of_month}&to={end_of_month + timedelta(days=7)}",
            headers=auth(slug, owner),
        )
    ).json()
    days = {d["date"]: d for d in span["barbers"][0]["days"]}
    assert all(
        days[(end_of_month + timedelta(days=n)).isoformat()]["intervals"] == [] for n in range(7)
    )
    after = end_of_month + timedelta(days=7)
    assert days[after.isoformat()]["intervals"] or after.isoweekday() == 7
