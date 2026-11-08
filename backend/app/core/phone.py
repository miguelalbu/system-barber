"""
Phone numbers in E.164 — the key the WhatsApp channel finds a client by, and
the format of every phone the shop stores (units, contact, clients).

Infrastructure, not a business rule, so it lives in `core` and any module may
use it (spec identity-units-hours, T5).

Kept dependency-free on purpose: the shops are Brazilian, so the only
inference is "10 or 11 digits = a Brazilian number with area code". Anything
international must come with a leading `+`.
"""

from __future__ import annotations

import re

_NON_DIGITS = re.compile(r"\D")


class InvalidPhone(ValueError):
    def __init__(self) -> None:
        super().__init__("Telefone inválido")


def normalize_phone(raw: str) -> str:
    """
    "(11) 98765-4321"  → "+5511987654321"
    "+55 11 98765-4321" → "+5511987654321"
    "+1 415 555 2671"  → "+14155552671"
    """
    text = raw.strip()
    digits = _NON_DIGITS.sub("", text)
    if text.startswith("+"):
        if 8 <= len(digits) <= 15:
            return f"+{digits}"
        raise InvalidPhone
    if len(digits) in (10, 11):
        return f"+55{digits}"
    if len(digits) in (12, 13) and digits.startswith("55"):
        return f"+{digits}"
    raise InvalidPhone
