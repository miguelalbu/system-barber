"""Shared bits of the scheduling tests."""

from datetime import date, timedelta

from tests.conftest import auth


def week(**days) -> dict:
    """`week(d1=[("09:00", "12:00")])` — days not given are off."""
    return {
        "days": [
            {
                "weekday": wd,
                "intervals": [{"starts_at": s, "ends_at": e} for s, e in days.get(f"d{wd}", [])],
            }
            for wd in range(1, 8)
        ]
    }


def next_weekday(iso_weekday: int, *, weeks_ahead: int = 2) -> date:
    """A future date on that weekday (ISO 1–7), far enough to never be 'past'."""
    start = date.today() + timedelta(weeks=weeks_ahead)
    return start + timedelta(days=(iso_weekday - start.isoweekday()) % 7)


async def main_unit(client, slug, token) -> str:
    return (await client.get("/tenant/units", headers=auth(slug, token))).json()[0]["id"]


async def new_unit(client, slug, token, name: str, **extra) -> str:
    resp = await client.post(
        "/tenant/units", headers=auth(slug, token), json={"name": name, **extra}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]
