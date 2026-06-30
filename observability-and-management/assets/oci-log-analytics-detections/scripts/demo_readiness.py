#!/usr/bin/env python3
"""Check live OCI Log Analytics demo readiness for multicloud + observability flows."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oci_config import (
    APPS_DIR,
    COMPARTMENT_ID,
    PROJECT_DIR,
    QUERIES_DIR,
    SOURCE_CANDIDATE_GROUPS,
    get_la_client,
    get_namespace,
    require_oci_config,
)
from oci_time import build_time_window
from redaction import redact_text

import oci


DEMO_QUERY_GROUPS = {
    "performance": [
        "apps/app_request_rate_by_endpoint.json",
        "apps/app_error_rate_by_service.json",
        "apps/app_slow_requests.json",
        "apps/app_service_health_timeline.json",
        "apps/app_cross_service_trace_correlation.json",
        "apps/app_db_performance_correlation.json",
        "apps/app_order_sync_pipeline.json",
    ],
    "operations": [
        "hunting/multicloud_geo_health_regional_map.json",
        "hunting/multicloud_geo_health_by_provider.json",
        "hunting/multicloud_geo_health_instance_detail.json",
        "hunting/multicloud_geo_health_unhealthy_regions.json",
        "hunting/multicloud_geo_health_tier_status.json",
    ],
    "security_correlation": [
        "apps/app_waf_signal_correlation.json",
        "apps/app_owasp_attack_detection.json",
        "apps/app_security_attack_by_ip.json",
        "hunting/browser_attack_frequency_analysis.json",
    ],
}

PROVIDER_EXPECTATIONS = ["OCI", "Azure", "AWS", "GCP"]


def build_log_source_clause(source_group: str) -> str:
    candidates = SOURCE_CANDIDATE_GROUPS[source_group]
    if len(candidates) == 1:
        return f"'Log Source' = '{candidates[0]}'"
    return "(" + " or ".join(f"'Log Source' = '{candidate}'" for candidate in candidates) + ")"


def load_query(query_file: str) -> dict:
    return json.loads((Path(PROJECT_DIR) / "queries" / query_file).read_text())


def execute_query_check(
    la_client,
    namespace: str,
    query: str,
    lookback: str,
    *,
    name: str,
    group: str | None = None,
    query_file: str | None = None,
) -> dict:
    time_start, time_end = build_time_window(lookback)
    result = {
        "name": name,
        "query": query,
        "ok": False,
        "rows": 0,
    }
    if group is not None:
        result["group"] = group
    if query_file is not None:
        result["query_file"] = query_file

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
        result["ok"] = bool(items)
        result["rows"] = len(items)
    except Exception as exc:
        result["error"] = redact_text(str(exc))

    return result


def check_data_surfaces(la_client, namespace: str, lookback: str) -> list[dict]:
    checks = []
    surfaces = [
        ("oci_audit", "OCI Audit"),
        ("cloud_guard", "Cloud Guard"),
        ("application_logs", "Application / Browser Telemetry"),
        ("multicloud_health", "Multicloud Health"),
    ]
    for source_group, label in surfaces:
        query = f"{build_log_source_clause(source_group)} | stats count as Events"
        checks.append(
            execute_query_check(
                la_client,
                namespace,
                query,
                lookback,
                name=label,
            )
        )

    provider_checks = []
    for provider in PROVIDER_EXPECTATIONS:
        query = (
            "'Log Source' = 'SOC Multicloud Health Logs' "
            f"and 'Cloud Provider' = '{provider}' | stats count as Heartbeats"
        )
        provider_checks.append(
            execute_query_check(
                la_client,
                namespace,
                query,
                lookback,
                name=f"Multicloud provider: {provider}",
            )
        )

    return checks + provider_checks


def check_demo_queries(la_client, namespace: str, lookback: str) -> list[dict]:
    checks = []
    for group_name, query_files in DEMO_QUERY_GROUPS.items():
        for query_file in query_files:
            payload = load_query(query_file)
            checks.append(
                execute_query_check(
                    la_client,
                    namespace,
                    payload["query"],
                    lookback,
                    name=payload["title"],
                    group=group_name,
                    query_file=query_file,
                )
            )
    return checks


def run_demo_readiness(lookback: str) -> dict:
    require_oci_config()
    la_client = get_la_client()
    namespace = get_namespace(la_client)

    surface_checks = check_data_surfaces(la_client, namespace, lookback)
    query_checks = check_demo_queries(la_client, namespace, lookback)

    failed = [check for check in surface_checks + query_checks if not check["ok"]]
    return {
        "lookback": lookback,
        "surface_checks": surface_checks,
        "query_checks": query_checks,
        "ok": not failed,
        "failed": failed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate live demo readiness in OCI Log Analytics")
    parser.add_argument("--lookback", default="24h", help="Lookback window for demo data presence checks")
    parser.add_argument("--dry-run", action="store_true", help="Print the checks without querying OCI")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output")
    args = parser.parse_args()

    if args.dry_run:
        print("=" * 60)
        print("Demo Readiness Checks")
        print("=" * 60)
        print("Data surfaces:")
        for source_group, label in [
            ("oci_audit", "OCI Audit"),
            ("cloud_guard", "Cloud Guard"),
            ("application_logs", "Application / Browser Telemetry"),
            ("multicloud_health", "Multicloud Health"),
        ]:
            print(f"  - {label}: {build_log_source_clause(source_group)} | stats count as Events")
        print("\nCritical demo queries:")
        for group_name, query_files in DEMO_QUERY_GROUPS.items():
            print(f"  [{group_name}]")
            for query_file in query_files:
                payload = load_query(query_file)
                print(f"    - {payload['title']} ({query_file})")
        return

    report = run_demo_readiness(args.lookback)

    if args.json:
        print(json.dumps(report, indent=2))
        raise SystemExit(0 if report["ok"] else 1)

    print("=" * 60)
    print("Live Demo Readiness")
    print("=" * 60)
    print(f"Lookback: {report['lookback']}")

    print("\nData surfaces")
    for check in report["surface_checks"]:
        status = "ERR" if check.get("error") else ("OK" if check["ok"] else "MISS")
        print(f"  [{status:4s}] {check['name']} ({check['rows']} row groups)")
        if check.get("error"):
            print(f"         {check['error']}")

    print("\nCritical demo queries")
    for check in report["query_checks"]:
        status = "ERR" if check.get("error") else ("OK" if check["ok"] else "MISS")
        print(f"  [{status:4s}] {check['group']}: {check['name']} ({check['rows']} rows)")
        if check.get("error"):
            print(f"         {check['error']}")

    if report["failed"]:
        print("\nMissing coverage")
        for check in report["failed"]:
            suffix = f" [{check['error']}]" if check.get("error") else ""
            print(f"  - {check['name']}{suffix}")

    raise SystemExit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
