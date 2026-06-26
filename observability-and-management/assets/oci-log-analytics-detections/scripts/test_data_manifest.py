#!/usr/bin/env python3
"""Helpers for maintaining the checked-in ``test_data/manifest.json`` file."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def _count_non_empty_lines(path: Path) -> int:
    with path.open() as f:
        return sum(1 for line in f if line.strip())


def rebuild_manifest(output_dir: Path) -> dict:
    """Rebuild ``manifest.json`` from all NDJSON files currently in ``output_dir``."""
    files = {}
    total_events = 0

    for path in sorted(output_dir.glob("*.jsonl")):
        count = _count_non_empty_lines(path)
        files[path.name] = {"event_count": count}
        total_events += count

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "files": files,
        "total_events": total_events,
    }

    manifest_path = output_dir / "manifest.json"
    with manifest_path.open("w") as f:
        json.dump(manifest, f, indent=2)

    return manifest
