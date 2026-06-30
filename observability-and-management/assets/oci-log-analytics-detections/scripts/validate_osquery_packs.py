#!/usr/bin/env python3
"""Validate OSQuery packs and emit the OCI migration bundle artifact."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parent.parent
PACK_DIR = PROJECT_DIR / "config" / "osquery" / "packs"
DEFAULT_BUNDLE = PROJECT_DIR / "queries" / "osquery_pack_bundle.json"
REQUIRED_PACKS = {
    "baseline-linux",
    "baseline-windows",
    "persistence",
    "network-exposure",
    "privilege-escalation",
    "web-server-compromise",
    "container-oke-host",
    "malware-triage",
}


def load_packs(pack_dir: Path = PACK_DIR) -> list[dict[str, Any]]:
    packs = []
    for path in sorted(pack_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["_path"] = path.relative_to(PROJECT_DIR).as_posix()
        packs.append(payload)
    return packs


def validate_packs(packs: list[dict[str, Any]]) -> list[str]:
    errors = []
    names = {pack.get("name") for pack in packs}
    missing = sorted(REQUIRED_PACKS - names)
    if missing:
        errors.append(f"missing required OSQuery pack(s): {', '.join(missing)}")
    for pack in packs:
        if not pack.get("name"):
            errors.append(f"{pack.get('_path', '<unknown>')}: missing pack name")
        queries = pack.get("queries", [])
        if not queries:
            errors.append(f"{pack.get('name', '<unknown>')}: pack has no queries")
        for query in queries:
            for key in ("id", "name", "sql", "expected_fields", "severity"):
                if not query.get(key):
                    errors.append(f"{pack.get('name')}/{query.get('id', '<unknown>')}: missing {key}")
            if not str(query.get("sql", "")).lower().strip().startswith("select"):
                errors.append(f"{pack.get('name')}/{query.get('id', '<unknown>')}: sql must start with SELECT")
    return errors


def build_bundle(packs: list[dict[str, Any]]) -> dict[str, Any]:
    linked_detections = [
        "cloud_guard_instance_security_high_severity_pivots.json",
        "cloud_guard_instance_security_findings_by_pack_query.json",
        "cloud_guard_instance_security_raw_result_detail.json",
    ]
    return {
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "config/osquery/packs",
        "parser_paths": {
            "cloud_guard_instance_security": "scripts/setup_log_sources.py:CGIS_FIELD_MAPPINGS",
            "synthetic_dataset": "test_data/cloud_guard_instance_security.jsonl",
        },
        "deployment_commands": [
            "python3 scripts/setup_log_sources.py --dry-run",
            "python3 scripts/generate_test_logs.py",
            "python3 scripts/ingest_test_data.py --file cloud_guard_instance_security.jsonl",
        ],
        "linked_detections": linked_detections,
        "packs": [
            {
                "name": pack["name"],
                "platform": pack.get("platform", ""),
                "description": pack.get("description", ""),
                "path": pack.get("_path", ""),
                "queries": pack.get("queries", []),
            }
            for pack in packs
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(DEFAULT_BUNDLE))
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    packs = load_packs()
    errors = validate_packs(packs)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    bundle = build_bundle(packs)
    if not args.validate_only:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote OSQuery bundle to {out_path}")
    else:
        print(f"Validated {len(packs)} OSQuery packs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
