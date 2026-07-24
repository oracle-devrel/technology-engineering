#!/usr/bin/env python3
"""Validate Cloud Guard Instance Security source, parser, and synthetic contracts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from scripts.field_dictionary import extract_query_fields  # noqa: E402
from scripts.generate_test_logs import generate_cloud_guard_instance_security_events  # noqa: E402
from scripts.oci_config import SOURCE_CANDIDATE_GROUPS  # noqa: E402
from scripts.setup_log_sources import CGIS_FIELD_MAPPINGS, CGIS_SOURCE_DISPLAY, OSQUERY_SOURCE_DISPLAY  # noqa: E402

QUERY_FILES = [
    PROJECT_DIR / "queries" / "cloud_guard_instance_security_pack_coverage.json",
    PROJECT_DIR / "queries" / "cloud_guard_instance_security_findings_by_host.json",
    PROJECT_DIR / "queries" / "cloud_guard_instance_security_findings_by_pack_query.json",
    PROJECT_DIR / "queries" / "cloud_guard_instance_security_high_severity_pivots.json",
    PROJECT_DIR / "queries" / "cloud_guard_instance_security_instance_to_query_link.json",
    PROJECT_DIR / "queries" / "cloud_guard_instance_security_raw_result_detail.json",
]


def main() -> int:
    errors = []
    mapped_fields = {field for field, _path, _seq in CGIS_FIELD_MAPPINGS}
    required_fields = {
        "Host Name",
        "Instance OCID",
        "Pack Name",
        "Pack Query ID",
        "Finding Name",
        "Finding Severity",
        "Finding Status",
        "OSQuery SQL",
        "OSQuery Finding",
        "Process Command Line",
    }
    missing = sorted(required_fields - mapped_fields)
    if missing:
        errors.append(f"CGIS parser missing fields: {', '.join(missing)}")
    candidates = SOURCE_CANDIDATE_GROUPS.get("cloud_guard_instance_security", [])
    if not candidates or candidates[0] != CGIS_SOURCE_DISPLAY or OSQUERY_SOURCE_DISPLAY not in candidates:
        errors.append("cloud_guard_instance_security source candidate group is not ordered correctly")
    events = generate_cloud_guard_instance_security_events()
    if len(events) < 4:
        errors.append("synthetic CGIS dataset must contain at least four findings")
    for event in events:
        if event.get("logType") != "cloud_guard_instance_security":
            errors.append("synthetic CGIS event missing logType=cloud_guard_instance_security")
        if not event.get("osquery", {}).get("sql"):
            errors.append("synthetic CGIS event missing osquery.sql")
    for path in QUERY_FILES:
        payload = json.loads(path.read_text(encoding="utf-8"))
        query = payload.get("query", "")
        if CGIS_SOURCE_DISPLAY not in query:
            errors.append(f"{path.name}: query does not target {CGIS_SOURCE_DISPLAY}")
        unsupported = sorted(extract_query_fields(query) - mapped_fields - {"Log Source", "Count", "Time"})
        if unsupported:
            errors.append(f"{path.name}: unsupported CGIS fields {unsupported}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"Validated Cloud Guard Instance Security contract: {len(events)} synthetic events, {len(QUERY_FILES)} queries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
