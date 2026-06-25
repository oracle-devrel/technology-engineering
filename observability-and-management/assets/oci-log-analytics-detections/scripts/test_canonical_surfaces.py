#!/usr/bin/env python3
"""Canonical surface fence: assert no detection-query JSON lives outside queries/**.

Allowed roots that may legitimately contain JSON (non-query JSON):
  - queries/     — canonical home for all detection, app, hunting, and sentinel queries
  - rules/       — Sigma YAML source files (converted to queries by convert_sigma.py)
  - config/      — field maps, source mappings, schema configs
  - schemas/     — JSON schema validation files
  - test_data/   — synthetic log events and test fixtures
  - webapp/      — Next.js app (package.json, node_modules, tsconfig, etc.)
  - docs/        — health-check artifacts, reference docs
  - stack/       — Terraform / Resource Manager state

Any .json file with a runnable query found outside these roots is a drift violation.
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path

# Resolve project root relative to this script
SCRIPTS_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = SCRIPTS_DIR.parent

sys.path.insert(0, str(SCRIPTS_DIR))
from query_artifacts import is_saved_search_query_file

# Roots where detection-query JSON is legitimately expected (or is non-query JSON)
ALLOWED_ROOT_NAMES = {
    "queries",
    "rules",
    "config",
    "schemas",
    "test_data",
    "webapp",
    "docs",
    "stack",
    "scripts",  # Python scripts — no query JSON expected here, but non-violating
}

# Top-level directories and name patterns to skip entirely (not scanned)
SKIP_DIR_NAMES = {
    ".git",
    ".claude",
    ".sigmahq",
    ".sentinel",
    ".venv",
    "venv",
    "__pycache__",
    "graphify-out",
    ".planning",
    "node_modules",
}


def _is_query_json(path: Path) -> bool:
    """Return True if the file looks like a runnable detection/hunting query."""
    if not is_saved_search_query_file(path):
        return False
    try:
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
        return isinstance(data, dict) and "query" in data
    except (json.JSONDecodeError, OSError):
        return False


def find_stray_query_jsons(project_dir: Path = PROJECT_DIR) -> list[Path]:
    """Walk the project tree and return query JSON files found outside allowed roots."""
    stray: list[Path] = []

    for entry in project_dir.iterdir():
        if not entry.is_dir():
            # Top-level .json files
            if entry.suffix == ".json" and _is_query_json(entry):
                stray.append(entry)
            continue

        # Skip allowed roots and hidden/generated directories
        if entry.name in ALLOWED_ROOT_NAMES or entry.name in SKIP_DIR_NAMES:
            continue
        if entry.name.startswith("."):
            continue

        # Any other top-level directory is unexpected for query JSON
        for path in entry.rglob("*.json"):
            if _is_query_json(path):
                stray.append(path)

    return sorted(stray)


class TestCanonicalSurfaces(unittest.TestCase):
    """Detection-query JSON must live exclusively under queries/**."""

    def test_no_stray_query_json_outside_queries(self) -> None:
        stray = find_stray_query_jsons()
        if stray:
            paths = "\n  ".join(str(p.relative_to(PROJECT_DIR)) for p in stray)
            self.fail(
                f"Found {len(stray)} detection-query JSON file(s) outside allowed roots.\n"
                f"Move them to queries/ (detection/app/hunting sub-dirs as appropriate):\n"
                f"  {paths}"
            )

    def test_queries_hunting_is_the_only_hunting_dir(self) -> None:
        """The top-level hunting/ directory must not exist."""
        toplevel_hunting = PROJECT_DIR / "hunting"
        self.assertFalse(
            toplevel_hunting.exists(),
            f"Top-level hunting/ directory still exists at {toplevel_hunting}. "
            "The canonical location is queries/hunting/.",
        )

    def test_legacy_logandetection_dirs_absent(self) -> None:
        """Legacy logandetectionqueries/ and logandetectionrules/ must not exist."""
        for legacy_dir in ("logandetectionqueries", "logandetectionrules"):
            legacy_path = PROJECT_DIR / legacy_dir
            self.assertFalse(
                legacy_path.exists(),
                f"Legacy directory {legacy_dir}/ still exists at {legacy_path}. "
                "Per CLAUDE.md, these must not contain hand-authored content.",
            )


if __name__ == "__main__":
    stray = find_stray_query_jsons()
    if stray:
        print(f"FAIL — {len(stray)} stray query JSON(s) found outside allowed roots:")
        for p in stray:
            print(f"  {p.relative_to(PROJECT_DIR)}")
        sys.exit(1)
    else:
        print("PASS — no stray query JSON found outside allowed roots.")

    toplevel_hunting = PROJECT_DIR / "hunting"
    if toplevel_hunting.exists():
        print(f"FAIL — top-level hunting/ still exists: {toplevel_hunting}")
        sys.exit(1)
    else:
        print("PASS — top-level hunting/ absent.")

    for legacy in ("logandetectionqueries", "logandetectionrules"):
        if (PROJECT_DIR / legacy).exists():
            print(f"FAIL — legacy dir {legacy}/ still exists.")
            sys.exit(1)
    print("PASS — legacy logandetection dirs absent.")
