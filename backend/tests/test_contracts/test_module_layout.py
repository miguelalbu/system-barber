"""
The shape every module must keep (rules.md, "Architecture"), checked on disk.

import-linter covers the layering inside a module and keeps `core` free of
modules; this file covers what it cannot express generically: the mandatory
folders, and that modules see each other only through `public.py`.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[2] / "app"
MODULES_DIR = APP / "modules"

MANDATORY_DIRS = ("router", "service", "repository", "model")
MANDATORY_FILES = ("__init__.py", "schemas.py", "public.py")

# Legacy flat layout, removed by the modular migration. Never recreate.
LEGACY_PATHS = (
    "models.py",
    "schemas.py",
    "deps.py",
    "db.py",
    "config.py",
    "security.py",
    "permissions.py",
    "seed.py",
    "routers",
)

MODULES = sorted(p.name for p in MODULES_DIR.iterdir() if p.is_dir() and not p.name.startswith("_"))


def test_there_is_at_least_one_module():
    assert MODULES, "app/modules/ has no module"


@pytest.mark.parametrize("module", MODULES)
def test_module_has_the_canonical_shape(module: str):
    root = MODULES_DIR / module
    missing = [d for d in MANDATORY_DIRS if not (root / d / "__init__.py").is_file()]
    missing += [f for f in MANDATORY_FILES if not (root / f).is_file()]
    assert not missing, f"module '{module}' is missing: {missing}"


def _has_code(path: Path) -> bool:
    """A file, or a folder holding Python files — a stale `__pycache__` does not count."""
    return path.is_file() or (path.is_dir() and any(path.rglob("*.py")))


def test_legacy_flat_layout_is_gone():
    present = [p for p in LEGACY_PATHS if _has_code(APP / p)]
    assert not present, f"legacy top-level paths came back: {present}"


def _imported_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.append(node.module)
    return names


def test_modules_import_each_other_only_through_public():
    violations: list[str] = []
    for module in MODULES:
        for path in (MODULES_DIR / module).rglob("*.py"):
            for name in _imported_modules(path):
                parts = name.split(".")
                if parts[:2] != ["app", "modules"] or len(parts) < 3:
                    continue
                other = parts[2]
                if other != module and parts[3:4] != ["public"]:
                    violations.append(f"{path.relative_to(APP)} imports {name}")
    assert not violations, "\n".join(violations)
