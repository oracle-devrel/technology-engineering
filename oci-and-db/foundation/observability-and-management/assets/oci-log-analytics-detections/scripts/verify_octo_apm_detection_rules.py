#!/usr/bin/env python3
"""Verify Octo APM workshop detection-rule queries against live Log Analytics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from deploy_dashboard import (
    get_la_client,
    get_namespace,
    load_query_info,
    validate_query_in_oci,
)
from octo_apm_workshop import DETECTION_RULE_QUERY_FILES

DEFAULT_JSON = Path("docs/health/octo-apm-detection-rules-live.json")


def verify_detection_rules(lookback: str, query_timeout: int) -> list[dict]:
    """Run the Octo detection-rule queries and return live result records."""
    client = get_la_client(timeout=(10, query_timeout))
    namespace = get_namespace(client)
    results = []
    for query_file in DETECTION_RULE_QUERY_FILES:
        payload = load_query_info(query_file)
        result = validate_query_in_oci(
            client,
            namespace,
            query_file,
            payload["query"],
            lookback,
            timeout=query_timeout,
        )
        result["status"] = (
            "HIT" if result["ok"] and result["rows"] > 0
            else "MISS" if result["ok"]
            else "ERROR"
        )
        results.append(result)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Live-verify Octo APM detection-rule queries"
    )
    parser.add_argument("--lookback", default="21d")
    parser.add_argument("--query-timeout", type=int, default=90)
    parser.add_argument("--json", default=str(DEFAULT_JSON))
    args = parser.parse_args()

    results = verify_detection_rules(args.lookback, args.query_timeout)
    for result in results:
        suffix = f" rows={result['rows']}"
        if result.get("error"):
            suffix += f" error={result['error'][:160]}"
        print(f"{result['status']} {result['query_file']}{suffix}")

    if args.json:
        output_path = Path(args.json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"JSON report written to: {output_path}")

    statuses = {result["status"] for result in results}
    if "ERROR" in statuses:
        return 2
    if "MISS" in statuses:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
