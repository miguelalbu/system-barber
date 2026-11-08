"""Brazilian national holidays of a year, the movable ones computed from Easter (Q-S01-2)."""

from __future__ import annotations

from datetime import date, timedelta

_FIXED = [
    (1, 1, "Confraternização Universal"),
    (4, 21, "Tiradentes"),
    (5, 1, "Dia do Trabalho"),
    (9, 7, "Independência do Brasil"),
    (10, 12, "Nossa Senhora Aparecida"),
    (11, 2, "Finados"),
    (11, 15, "Proclamação da República"),
    (11, 20, "Dia Nacional de Zumbi e da Consciência Negra"),
    (12, 25, "Natal"),
]


def easter(year: int) -> date:
    """Gregorian Easter Sunday (anonymous algorithm, a.k.a. Meeus/Jones/Butcher)."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7  # noqa: E741 — the algorithm's own name
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


def national_holidays(year: int) -> list[tuple[date, str]]:
    """Fixed plus movable ones (Carnival Monday/Tuesday, Good Friday, Corpus Christi), sorted."""
    e = easter(year)
    movable = [
        (e - timedelta(days=48), "Carnaval (segunda-feira)"),
        (e - timedelta(days=47), "Carnaval (terça-feira)"),
        (e - timedelta(days=2), "Sexta-feira Santa"),
        (e + timedelta(days=60), "Corpus Christi"),
    ]
    fixed = [(date(year, m, d), name) for m, d, name in _FIXED]
    return sorted(fixed + movable)
