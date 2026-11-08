"""Weekly opening hours of a unit (spec S01)."""

from tests.conftest import auth, member_token, owner_token


def _week(**days) -> dict:
    """`_week(d1=[("09:00", "12:00")])` — days not given are closed."""
    return {
        "days": [
            {
                "weekday": wd,
                "intervals": [{"opens_at": o, "closes_at": c} for o, c in days.get(f"d{wd}", [])],
            }
            for wd in range(1, 8)
        ]
    }


async def _main_unit(client, slug, token) -> str:
    return (await client.get("/tenant/units", headers=auth(slug, token))).json()[0]["id"]


async def test_replace_the_week(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    path = f"/tenant/units/{await _main_unit(client, slug, owner)}/hours"
    split = [("13:00", "19:00"), ("09:00", "12:00")]  # out of order on purpose
    resp = await client.put(
        path, headers=auth(slug, owner), json=_week(d1=split, d6=[("08:00", "14:30")])
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["warning"] is None
    assert body["days"][0]["intervals"] == [
        {"opens_at": "09:00", "closes_at": "12:00"},
        {"opens_at": "13:00", "closes_at": "19:00"},
    ]
    assert body["days"][1]["intervals"] == []  # Tuesday not sent: closed
    assert (await client.get(path, headers=auth(slug, owner))).json() == body


async def test_validation(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    path = f"/tenant/units/{await _main_unit(client, slug, owner)}/hours"
    six_days = _week()
    six_days["days"].pop()
    repeated = _week()
    repeated["days"][6]["weekday"] = 1
    for body in (
        six_days,
        repeated,
        _week(d1=[("09:00", "12:00"), ("12:00", "13:00")]),  # touching
        _week(d1=[("09:00", "12:00"), ("11:00", "13:00")]),  # overlapping
        _week(d1=[("08:00", "09:00"), ("10:00", "11:00"), ("12:00", "13:00"), ("14:00", "15:00")]),
        _week(d1=[("09:03", "12:00")]),  # not a multiple of 5 minutes
        _week(d1=[("12:00", "09:00")]),
    ):
        assert (await client.put(path, headers=auth(slug, owner), json=body)).status_code == 422


async def test_whole_week_closed_warns(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    path = f"/tenant/units/{await _main_unit(client, slug, owner)}/hours"
    resp = await client.put(path, headers=auth(slug, owner), json=_week())
    assert resp.status_code == 200
    assert resp.json()["warning"] == "Unidade sem nenhum horário de funcionamento"


async def test_unit_configure(client, core_key, slug):
    owner = await owner_token(client, core_key, slug)
    main = await _main_unit(client, slug, owner)
    other = (
        await client.post("/tenant/units", headers=auth(slug, owner), json={"name": "Zona Sul"})
    ).json()["id"]
    manager = await member_token(
        client, slug, owner, role="manager", email="mgr@x.com", unit_ids=[main]
    )
    desk = await member_token(client, slug, owner, role="receptionist", email="desk@x.com")

    week = _week(d1=[("10:00", "18:00")])
    ok = await client.put(f"/tenant/units/{main}/hours", headers=auth(slug, manager), json=week)
    assert ok.status_code == 200
    away = await client.put(f"/tenant/units/{other}/hours", headers=auth(slug, manager), json=week)
    assert away.status_code == 404
    denied = await client.put(f"/tenant/units/{main}/hours", headers=auth(slug, desk), json=week)
    assert denied.status_code == 403
    # Reading is for everyone with access to the unit.
    assert (
        await client.get(f"/tenant/units/{main}/hours", headers=auth(slug, desk))
    ).status_code == 200
