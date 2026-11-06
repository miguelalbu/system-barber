"""
Golden snapshots of the backend's external contracts.

A failing snapshot means behaviour changed: find the cause, never regenerate to
make it pass. Regenerate only for an intended, reviewed change:

    UPDATE_CONTRACT_SNAPSHOTS=1 pytest tests/test_contracts
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"


def assert_matches_snapshot(name: str, current: Any) -> None:
    path = SNAPSHOT_DIR / f"{name}.json"
    rendered = json.dumps(current, indent=2, sort_keys=True, ensure_ascii=False) + "\n"

    if os.getenv("UPDATE_CONTRACT_SNAPSHOTS") == "1":
        path.write_text(rendered, encoding="utf-8")
        return

    assert path.exists(), (
        f"Missing snapshot {path.name}: generate it with UPDATE_CONTRACT_SNAPSHOTS=1"
    )

    expected = path.read_text(encoding="utf-8")
    assert rendered == expected, (
        f"Contract snapshot '{name}' changed. If the change is intended and reviewed, "
        "regenerate with UPDATE_CONTRACT_SNAPSHOTS=1 and record it in the spec."
    )
