#!/usr/bin/env python3
"""Validate every detection/hunting/app query against the live OCI Log Analytics
*parser* (syntax + field references) — fast complement to smoke_test_all_queries.

Unlike the execution-based smoke test (one isolated child per query, reloads the
field inventory each time, depends on ingested data), this runner loads a single
LA client and calls the ``parse_query`` API per query. ``parse`` validates the
Logan QL grammar and resolves every referenced field/source against live LA
metadata WITHOUT executing the search, so it isolates "is this query valid?"
(ERROR) from "is there matching data?" (the smoke test's MISS).

Usage:
    OCI_PROFILE=cap python3 scripts/parse_validate_all_queries.py [--json out.json]

Exit codes:
    0 = every query parses
    1 = at least one query fails to parse (invalid syntax/field/source)
    3 = OCI auth / namespace lookup failed
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "scripts"))

import oci  # noqa: E402
from oci_config import LA_NAMESPACE, get_la_client, require_oci_config  # noqa: E402
from redaction import redact_text  # noqa: E402
from query_artifacts import is_saved_search_query_file  # noqa: E402
from obs_logging import get_logger  # noqa: E402

log = get_logger("parse_validate_all_queries")

QUERIES_DIR = PROJECT_DIR / "queries"


def _iter_query_files():
    for path in sorted(QUERIES_DIR.rglob("*.json")):
        if is_saved_search_query_file(path):
            yield path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", help="write a JSON report to this path")
    args = parser.parse_args(argv)

    try:
        require_oci_config()
        client = get_la_client()
        namespace = LA_NAMESPACE
    except Exception as exc:  # noqa: BLE001
        log.error("parse_validate.oci_auth_failed", extra={"error": str(exc)})
        print(f"OCI config/auth failed: {exc}", file=sys.stderr)
        return 3

    models = oci.log_analytics.models
    nr = oci.retry.NoneRetryStrategy()
    results = []
    by_dir = defaultdict(Counter)

    files = list(_iter_query_files())
    print(f"parse-validating {len(files)} queries against namespace {namespace} ...")
    for i, path in enumerate(files, 1):
        try:
            spec = json.loads(path.read_text())
        except Exception as exc:  # noqa: BLE001
            results.append({"file": str(path), "status": "ERROR", "error": f"bad json: {exc}"})
            continue
        query = spec.get("query")
        rel_dir = path.relative_to(QUERIES_DIR).parts[0] if len(path.relative_to(QUERIES_DIR).parts) > 1 else "."
        if not query:
            by_dir[rel_dir]["SKIP"] += 1
            results.append({"file": str(path), "status": "SKIP", "error": "no query field"})
            continue
        try:
            client.parse_query(
                namespace_name=namespace,
                parse_query_details=models.ParseQueryDetails(query_string=query, sub_system="LOG"),
                retry_strategy=nr,
            )
            by_dir[rel_dir]["PASS"] += 1
            results.append({"file": str(path), "status": "PASS"})
        except oci.exceptions.ServiceError as exc:
            by_dir[rel_dir]["FAIL"] += 1
            results.append({"file": str(path), "status": "FAIL",
                            "error": redact_text(getattr(exc, "message", str(exc))),
                            "query": redact_text(query)})
        if i % 50 == 0:
            print(f"  {i}/{len(files)} ...")

    total = Counter(r["status"] for r in results)
    print("\n=== per-directory ===")
    for d in sorted(by_dir):
        c = by_dir[d]
        print(f"  {d:24} PASS={c['PASS']:4} FAIL={c['FAIL']:3} SKIP={c['SKIP']:3}")
    print(f"\n=== total: PASS={total['PASS']} FAIL={total['FAIL']} SKIP={total['SKIP']} (of {len(files)}) ===")
    log.info(
        "parse_validate.done",
        extra={"pass": total["PASS"], "fail": total["FAIL"], "skip": total["SKIP"], "total": len(files)},
    )

    fails = [r for r in results if r["status"] == "FAIL"]
    if fails:
        print("\n=== FAILURES ===")
        for r in fails[:60]:
            print(f"  {Path(r['file']).name}: {r['error'][:90]}")

    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=2))
        print(f"\nreport -> {args.json}")

    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
