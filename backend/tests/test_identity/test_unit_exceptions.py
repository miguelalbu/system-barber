"""Calendar exceptions, suggested holidays and the effective calendar (spec S01)."""

from datetime import date, time, timedelta

from app.core.database import tenant_session
from app.modules.identity.public import get_unit_calendar, schema_name_for
from app.modules.identity.service._holidays import easter, national_holidays
from tests.conftest import auth, member_token, owner_token

SOON = date.today() + timedelta(days=30)


def _day(offset: int) -> str:
    return (SOON + timedelta(days=offset)).isoformat()


async def _unit(client, slug, token, name: str | None = None) -> str:
    if name is None:
        return (await client.get("/tenant/units", headers=auth(slug, token))).json()[0]["id"]
    resp = await client.post("/tenant/units", headers=auth(slug, token), json={"name": name})
    return resp.json()["id"]


async def _post(client, slug, token, **body):
    return await client.post("/tenant/unit-exceptions", headers=auth(slug, token), json=body)


async def test_create_for_several_units_and_edit(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    main, sul = await _unit(client, slug, owner), await _unit(client, slug, owner, "Zona Sul")

    resp = await _post(
        client,
        slug,
        owner,
        unit_ids=[main, sul, main],
        starts_on=_day(0),
        ends_on=_day(2),
        kind="closed",
        reason="  Reforma ",
    )
    assert resp.status_code == 201, resp.text
    created = resp.json()
    assert sorted(e["unit_id"] for e in created) == sorted([main, sul])  # duplicates ignored
    assert created[0]["reason"] == "Reforma"

    # The same unit cannot have two exceptions on the same days.
    overlap = await _post(
        client, slug, owner, unit_ids=[main], starts_on=_day(2), ends_on=_day(3), kind="closed"
    )
    assert overlap.status_code == 409

    listed = (
        await client.get(f"/tenant/unit-exceptions?unit_id={main}", headers=auth(slug, owner))
    ).json()
    assert [e["id"] for e in listed] == [e["id"] for e in created if e["unit_id"] == main]

    path = f"/tenant/unit-exceptions/{listed[0]['id']}"
    special = await client.patch(
        path,
        headers=auth(slug, owner),
        json={"kind": "special_hours", "opens_at": "08:00", "closes_at": "14:00"},
    )
    assert special.status_code == 200, special.text
    assert (special.json()["opens_at"], special.json()["closes_at"]) == ("08:00", "14:00")
    back = await client.patch(path, headers=auth(slug, owner), json={"kind": "closed"})
    assert back.json()["opens_at"] is None  # a closed day drops the special hours

    assert (await client.delete(path, headers=auth(slug, owner))).status_code == 204
    assert (
        await client.get(f"/tenant/unit-exceptions?unit_id={main}", headers=auth(slug, owner))
    ).json() == []


async def test_rules(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    main = await _unit(client, slug, owner)
    yesterday = (date.today() - timedelta(days=2)).isoformat()
    base = {"unit_ids": [main], "starts_on": _day(0), "ends_on": _day(0)}
    for body in (
        {**base, "kind": "special_hours"},  # needs hours
        {**base, "kind": "closed", "opens_at": "09:00", "closes_at": "12:00"},
        {**base, "kind": "special_hours", "opens_at": "14:00", "closes_at": "09:00"},
        {**base, "ends_on": _day(-1), "kind": "closed"},
        {**base, "starts_on": yesterday, "ends_on": yesterday, "kind": "closed"},  # past
        {**base, "ends_on": _day(366), "kind": "closed"},  # more than 366 days
    ):
        assert (await _post(client, slug, owner, **body)).status_code == 422, body


async def test_scope_all_or_nothing(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    main, sul = await _unit(client, slug, owner), await _unit(client, slug, owner, "Zona Sul")
    manager = await member_token(
        client, slug, owner, role="manager", email="mgr@x.com", unit_ids=[main]
    )

    body = {"starts_on": _day(0), "ends_on": _day(0), "kind": "closed"}
    mixed = await _post(client, slug, manager, unit_ids=[main, sul], **body)
    assert mixed.status_code == 400
    assert (await client.get("/tenant/unit-exceptions", headers=auth(slug, owner))).json() == []
    assert (await _post(client, slug, manager, unit_ids=[main], **body)).status_code == 201

    desk = await member_token(client, slug, owner, role="receptionist", email="desk@x.com")
    assert (await _post(client, slug, desk, unit_ids=[main], **body)).status_code == 403


def test_movable_holidays():
    assert easter(2026) == date(2026, 4, 5)
    assert easter(2027) == date(2027, 3, 28)
    names_2026 = dict((n, d) for d, n in national_holidays(2026))
    assert names_2026["Carnaval (terça-feira)"] == date(2026, 2, 17)
    assert names_2026["Sexta-feira Santa"] == date(2026, 4, 3)
    assert names_2026["Corpus Christi"] == date(2026, 6, 4)
    names_2027 = dict((n, d) for d, n in national_holidays(2027))
    assert names_2027["Carnaval (segunda-feira)"] == date(2027, 2, 8)
    assert names_2027["Corpus Christi"] == date(2027, 5, 27)
    assert len(national_holidays(2026)) == 13


async def test_suggested_holidays(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    main = await _unit(client, slug, owner)
    year = date.today().year + 1
    christmas = date(year, 12, 25).isoformat()
    await _post(
        client, slug, owner, unit_ids=[main], starts_on=christmas, ends_on=christmas, kind="closed"
    )

    holidays = (await client.get(f"/tenant/holidays?year={year}", headers=auth(slug, owner))).json()
    by_date = {h["date"]: h for h in holidays}
    assert by_date[christmas]["name"] == "Natal"
    assert by_date[christmas]["already_closed_unit_ids"] == [main]
    assert by_date[f"{year}-01-01"]["already_closed_unit_ids"] == []


async def test_effective_calendar(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    # A unit in another timezone, around the US daylight-saving switch of next year.
    unit = (
        await client.post(
            "/tenant/units",
            headers=auth(slug, owner),
            json={"name": "NY", "timezone": "America/New_York"},
        )
    ).json()["id"]
    year = date.today().year + 1
    march = date(year, 3, 1)
    switch = march + timedelta(days=(6 - march.weekday()) % 7 + 7)  # second Sunday of March
    monday, tuesday = switch + timedelta(days=1), switch + timedelta(days=2)
    await _post(
        client,
        slug,
        owner,
        unit_ids=[unit],
        starts_on=monday.isoformat(),
        ends_on=monday.isoformat(),
        kind="closed",
        reason="Inventário",
    )
    await _post(
        client,
        slug,
        owner,
        unit_ids=[unit],
        starts_on=tuesday.isoformat(),
        ends_on=tuesday.isoformat(),
        kind="special_hours",
        opens_at="10:00",
        closes_at="14:00",
    )

    async with tenant_session(schema_name_for(slug)) as session:
        cal = await get_unit_calendar(
            session,
            __import__("uuid").UUID(unit),
            switch - timedelta(days=1),
            tuesday + timedelta(days=1),
        )

    assert cal.timezone.key == "America/New_York"
    assert cal.days[switch - timedelta(days=1)] == [(time(9), time(19))]  # Saturday
    assert cal.days[switch] == []  # Sunday: not in the default week
    assert cal.days[monday] == [] and cal.closed_reason[monday] == "Inventário"
    assert cal.days[tuesday] == [(time(10), time(14))]
    assert cal.days[tuesday + timedelta(days=1)] == [(time(9), time(19))]
    assert switch not in cal.closed_reason  # closed by the week, not by an exception
