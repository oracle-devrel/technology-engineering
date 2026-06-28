#!/usr/bin/env python3
"""Audit OCI Log Analytics queries for parser errors and live result coverage."""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from detection_rule_creator import build_catalog
from oci_config import COMPARTMENT_ID, get_la_client, get_namespace, require_oci_config
from oci_time import build_time_window
from redaction import redact_text

import oci


def normalize_query_file_filter(files: list[str] | None) -> set[str]:
    """Return normalized query-file selectors for exact path or basename matches."""
    return {
        file.replace("\\", "/").removeprefix("./")
        for file in files or []
    }


def load_specs(eligible_only: bool, files: list[str] | None = None) -> list[dict]:
    """Load query specs from the detection-rule catalog."""
    catalog = build_catalog()
    specs = catalog["specs"]
    if eligible_only:
        specs = [spec for spec in specs if spec["eligible"]]
    file_filter = normalize_query_file_filter(files)
    if file_filter:
        specs = [
            spec for spec in specs
            if spec["query_file"] in file_filter
            or os.path.basename(spec["query_file"]) in file_filter
        ]
    return specs


def execute_query(la_client, namespace: str, query: str, lookback: str) -> dict:
    """Run a single OCI Log Analytics query and capture result metadata."""
    time_start, time_end = build_time_window(lookback)
    try:
        response = la_client.query(
            namespace_name=namespace,
            query_details=oci.log_analytics.models.QueryDetails(
                compartment_id=COMPARTMENT_ID,
                query_string=query,
                sub_system="LOG",
                time_filter=oci.log_analytics.models.TimeRange(
                    time_start=time_start,
                    time_end=time_end,
                    time_zone="UTC",
                ),
                max_total_count=50,
            ),
        ).data
        items = getattr(response, "items", []) or []
        return {"rows": len(items), "ok": True, "empty": len(items) == 0}
    except Exception as exc:
        return {"rows": 0, "ok": False, "empty": False, "error": redact_text(str(exc))}


def audit_queries(lookback: str, eligible_only: bool, files: list[str] | None = None) -> dict:
    """Audit all configured queries against live OCI Log Analytics."""
    require_oci_config()
    la_client = get_la_client()
    namespace = get_namespace(la_client)
    specs = load_specs(eligible_only, files)

    results = []
    for spec in specs:
        outcome = execute_query(la_client, namespace, spec["query"], lookback)
        results.append({
            "query_file": spec["query_file"],
            "title": spec["title"],
            "eligible": spec["eligible"],
            "rows": outcome["rows"],
            "ok": outcome["ok"],
            "empty": outcome["empty"],
            "error": outcome.get("error"),
        })

    errors = [result for result in results if result.get("error")]
    empty = [result for result in results if result["ok"] and result["empty"]]
    populated = [result for result in results if result["ok"] and not result["empty"]]

    return {
        "lookback": lookback,
        "eligible_only": eligible_only,
        "requested_files": files or [],
        "total_queries": len(results),
        "queries_with_results": len(populated),
        "queries_empty": len(empty),
        "queries_with_errors": len(errors),
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit OCI Log Analytics queries for live results")
    parser.add_argument("--lookback", default="7d", help="Lookback window for query execution")
    parser.add_argument("--eligible-only", action="store_true",
                        help="Only audit scheduled-search eligible detection queries")
    parser.add_argument("--files", nargs="*", default=None,
                        help="Optional query JSON paths or basenames to audit")
    parser.add_argument("--out", help="Optional JSON output path")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON to stdout")
    args = parser.parse_args()

    report = audit_queries(args.lookback, args.eligible_only, args.files)

    if args.out:
        with open(args.out, "w") as f:
            json.dump(report, f, indent=2)

    if args.json:
        print(json.dumps(report, indent=2))
        raise SystemExit(0 if report["queries_with_errors"] == 0 else 1)

    print("=" * 60)
    print("OCI Log Analytics Query Audit")
    print("=" * 60)
    print(f"Lookback:            {report['lookback']}")
    print(f"Eligible only:       {report['eligible_only']}")
    print(f"Total queries:       {report['total_queries']}")
    print(f"Queries with rows:   {report['queries_with_results']}")
    print(f"Queries empty:       {report['queries_empty']}")
    print(f"Queries with errors: {report['queries_with_errors']}")

    if report["queries_with_errors"]:
        print("\nErrors")
        for result in report["results"]:
            if result.get("error"):
                print(f"  [ERR] {result['query_file']}: {result['error']}")

    if report["queries_empty"]:
        print("\nNo data returned")
        for result in report["results"]:
            if result["ok"] and result["empty"]:
                print(f"  [MISS] {result['query_file']}")

    raise SystemExit(0 if report["queries_with_errors"] == 0 else 1)


if __name__ == "__main__":
    main()
