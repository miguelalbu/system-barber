"""docs/PERMISSIONS_MAP.md must show exactly the map in permissions.py."""

from __future__ import annotations

import os
import re
from pathlib import Path

from app.modules.identity.model import Role
from app.modules.identity.permissions import PERMISSIONS_BY_ROLE, Permission

DOC = Path(__file__).resolve().parents[2] / "docs" / "PERMISSIONS_MAP.md"
BLOCK = re.compile(r"(<!-- BEGIN:permissions -->\n)(.*?)(<!-- END:permissions -->)", re.S)


def render_table() -> str:
    roles = list(Role)
    lines = [
        "| Permissão | " + " | ".join(f"`{r.value}`" for r in roles) + " |",
        "|---|" + "---|" * len(roles),
    ]
    for permission in Permission:
        cells = []
        for role in roles:
            scope = PERMISSIONS_BY_ROLE[role].get(permission)
            cells.append(scope.value if scope else "—")
        lines.append(f"| `{permission.value}` | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def test_permissions_doc_matches_code():
    text = DOC.read_text(encoding="utf-8")
    match = BLOCK.search(text)
    assert match, "PERMISSIONS_MAP.md lost its BEGIN/END:permissions markers"

    expected = render_table()
    if os.getenv("UPDATE_CONTRACT_SNAPSHOTS") == "1":
        DOC.write_text(BLOCK.sub(lambda m: m.group(1) + expected + m.group(3), text), "utf-8")
        return

    assert match.group(2) == expected, (
        "docs/PERMISSIONS_MAP.md is out of date with permissions.py — "
        "regenerate with UPDATE_CONTRACT_SNAPSHOTS=1 and review the diff"
    )
