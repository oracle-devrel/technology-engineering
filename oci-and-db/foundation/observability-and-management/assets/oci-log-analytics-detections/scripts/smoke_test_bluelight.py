#!/usr/bin/env python3
"""Smoke-test all BLUELIGHT (S0657 / APT37) detection widgets against OCI Log Analytics.

Runs each widget query from ``deploy_dashboard.py`` BLUELIGHT block plus the kill-chain
hunt and reports HIT / MISS / ERROR per widget so demo content is verified before
redeploy.

Usage:
    python3 scripts/smoke_test_bluelight.py [--lookback 30d] [--json]

Exit codes:
    0 = every widget returned at least one row
    1 = at least one widget returned zero rows (silent-zero risk for showcase)
    2 = OCI client / namespace lookup failed
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "scripts"))

from oci_config import (  # noqa: E402  (after sys.path mutation)
    COMPARTMENT_ID,
    LA_NAMESPACE,
    TENANCY_ID,
    get_la_client,
    require_oci_config,
)

QUERIES_DIR = PROJECT_DIR / "queries"

BLUELIGHT_WIDGETS: list[tuple[str, str]] = [
    ("APT37: Drive-by Compromise", "bluelight_drive_by_compromise.json"),
    ("APT37: Browser Child Process", "bluelight_browser_child_process.json"),
    ("APT37: Obfuscated Commandline", "bluelight_obfuscated_commandline.json"),
    ("APT37: Graph API C2", "bluelight_graph_api_c2.json"),
    ("APT37: WMI System Discovery", "bluelight_system_discovery.json"),
    ("APT37: Registry Enumeration", "bluelight_registry_enumeration.json"),
    ("APT37: File Discovery", "bluelight_file_discovery.json"),
    ("APT37: Screen Capture", "bluelight_screen_capture.json"),
    ("APT37: Browser Credential Theft", "bluelight_browser_credential_theft.json"),
    ("APT37: Ingress Tool Transfer", "bluelight_ingress_tool_transfer.json"),
    ("APT37: OneDrive Exfiltration", "bluelight_onedrive_exfiltration.json"),
    ("YARA: PDB Path Indicators", "bluelight_yara_pdb_strings.json"),
    ("YARA: System Recon JSON", "bluelight_yara_system_recon.json"),
    ("YARA: Cookie Theft (Chrome/Edge)", "bluelight_yara_cookie_theft.json"),
    ("YARA: Keylogger Staging", "bluelight_yara_keylogger.json"),
    ("YARA: Google App C2", "bluelight_yara_google_c2.json"),
    ("Hunt: BLUELIGHT Kill Chain", "hunting/bluelight_apt37_kill_chain.json"),
]


@dataclass(frozen=True)
class WidgetResult:
    title: str
    query_file: str
    row_count: int
    status: str
    query: str = field(repr=False)
    error: str | None = None


def _parse_lookback(value: str) -> timedelta:
    units = {"m": "minutes", "h": "hours", "d": "days"}
    if not value or value[-1] not in units:
        raise ValueError(f"Invalid lookback '{value}'. Use forms like 60m, 6h, 30d.")
    return timedelta(**{units[value[-1]]: int(value[:-1])})


def _time_window(lookback: str) -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    return now - _parse_lookback(lookback), now


def _load_query(query_file: str) -> dict:
    path = QUERIES_DIR / query_file
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _strip_pipe_clauses(query: str) -> str:
    """For row counting we keep only the filter; aggregations like ``stats`` reduce output."""
    return query.split("|", 1)[0].strip()


def _run_query(la_client, namespace: str, raw_query: str,
               start: datetime, end: datetime) -> tuple[int, str | None]:
    import oci
    try:
        result = la_client.query(
            namespace_name=namespace,
            query_details=oci.log_analytics.models.QueryDetails(
                compartment_id=COMPARTMENT_ID,
                query_string=raw_query,
                sub_system="LOG",
                max_total_count=50,
                time_filter=oci.log_analytics.models.TimeRange(
                    time_start=start,
                    time_end=end,
                    time_zone="UTC",
                ),
            ),
        )
        items = getattr(result.data, "items", []) or []
        return len(items), None
    except Exception as exc:  # noqa: BLE001 — surface every failure
        return -1, str(exc)


def smoke_test(lookback: str = "30d") -> list[WidgetResult]:
    require_oci_config()
    la_client = get_la_client()
    namespace = LA_NAMESPACE
    if not namespace:
        ns_resp = la_client.list_namespaces(compartment_id=TENANCY_ID).data
        if not ns_resp.items:
            raise RuntimeError("No Log Analytics namespace found in tenancy.")
        namespace = ns_resp.items[0].namespace_name

    start, end = _time_window(lookback)
    out: list[WidgetResult] = []
    for title, query_file in BLUELIGHT_WIDGETS:
        spec = _load_query(query_file)
        # Strip post-filter aggregations to count raw matches; widget itself keeps stats.
        raw_query = _strip_pipe_clauses(spec["query"])
        count, err = _run_query(la_client, namespace, raw_query, start, end)
        if err:
            status = "ERROR"
        elif count > 0:
            status = "HIT"
        else:
            status = "MISS"
        out.append(WidgetResult(
            title=title, query_file=query_file,
            row_count=count, status=status,
            query=raw_query, error=err,
        ))
    return out


def _print_table(results: Iterable[WidgetResult]) -> None:
    print("\n" + "=" * 78)
    print(f"{'STATUS':6s}  {'COUNT':>5s}  TITLE")
    print("-" * 78)
    for r in results:
        print(f"{r.status:6s}  {r.row_count:>5d}  {r.title}")
        if r.error:
            print(f"        ↳ {r.error}")
    print("=" * 78)


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test BLUELIGHT widgets")
    parser.add_argument("--lookback", default="30d",
                        help="Lookback window (e.g. 60m, 6h, 30d). Default: 30d")
    parser.add_argument("--json", action="store_true",
                        help="Emit machine-readable JSON instead of a table")
    args = parser.parse_args()

    try:
        results = smoke_test(args.lookback)
    except Exception as exc:  # noqa: BLE001
        print(f"FATAL: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps([
            {"title": r.title, "query_file": r.query_file,
             "row_count": r.row_count, "status": r.status,
             "error": r.error}
            for r in results
        ], indent=2))
    else:
        _print_table(results)
        misses = [r for r in results if r.status != "HIT"]
        print(f"\n{len(results) - len(misses)}/{len(results)} widgets returning rows.")
        if misses:
            print("Missing data for:")
            for r in misses:
                print(f"  - {r.title} ({r.status})")

    return 0 if all(r.status == "HIT" for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
