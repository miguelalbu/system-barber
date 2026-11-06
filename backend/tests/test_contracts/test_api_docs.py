"""docs/api/ must be exactly what tools/api_docs.py generates from the current OpenAPI."""

from __future__ import annotations

import os

from tools.api_docs import DOCS_DIR, render_all


def test_api_docs_match_the_code():
    expected = render_all()

    if os.getenv("UPDATE_CONTRACT_SNAPSHOTS") == "1":
        DOCS_DIR.mkdir(parents=True, exist_ok=True)
        for name, content in expected.items():
            (DOCS_DIR / name).write_text(content, encoding="utf-8")

    on_disk = {p.name: p.read_text(encoding="utf-8") for p in DOCS_DIR.glob("*.md")}
    assert set(on_disk) == set(expected), (
        "docs/api has missing or extra files — run `make docs-api`"
    )
    stale = [name for name, content in expected.items() if on_disk[name] != content]
    assert not stale, f"docs/api is out of date ({stale}) — run `make docs-api`"
