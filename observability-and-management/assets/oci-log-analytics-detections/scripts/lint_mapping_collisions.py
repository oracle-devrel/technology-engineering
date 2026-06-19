#!/usr/bin/env python3
"""Generate or check Sentinel mapping collision inventory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from scripts.kql.mapping_loader import build_collision_report, load_mapping
DEFAULT_OUTPUT = PROJECT_DIR / "queries" / "mapping_collisions.json"


def _render(report: dict) -> str:
    return json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true", help="Fail when the output file is stale.")
    args = parser.parse_args()

    report = build_collision_report(load_mapping())
    rendered = _render(report)
    if args.check:
        if not args.output.exists():
            print(f"missing mapping collision report: {args.output}")
            return 1
        current = args.output.read_text(encoding="utf-8")
        if current != rendered:
            print(f"stale mapping collision report: {args.output}")
            return 1
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
