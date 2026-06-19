#!/usr/bin/env python3
"""Verify each redeployed SOC dashboard has the expected widgets and that
embedded saved-search queries return rows from live OCI Log Analytics.

For every dashboard in ``deploy_dashboard.DASHBOARDS``:

1. Fetch the deployed Management Dashboard by display name.
2. Compare the widget count against the expected count from the source.
3. For each embedded saved search, run its queryString against live OCI LA
   over the configured lookback window and report HIT / MISS / ERROR.

Usage:
    python3 scripts/verify_deployed_dashboards.py [--lookback 21d] [--json out.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import nullcontext
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import threading

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "scripts"))

from deploy_dashboard import DASHBOARDS, query_deadline, select_dashboards  # noqa: E402
from redaction import redact_text  # noqa: E402
from oci_config import (  # noqa: E402
    COMPARTMENT_ID,
    LA_NAMESPACE,
    TENANCY_ID,
    get_dashboard_client,
    get_la_client,
    require_oci_config,
)


@dataclass
class WidgetVerification:
    dashboard: str
    widget: str
    row_count: int
    status: str  # HIT | MISS | ERROR
    error: str | None = None


_THREAD_LOCAL = threading.local()


def _parse_lookback(value: str) -> timedelta:
    units = {"m": "minutes", "h": "hours", "d": "days"}
    return timedelta(**{units[value[-1]]: int(value[:-1])})


def _get_thread_la_client(query_timeout: int):
    """Return one Log Analytics client per worker thread."""
    cached = getattr(_THREAD_LOCAL, "la_client", None)
    cached_timeout = getattr(_THREAD_LOCAL, "query_timeout", None)
    if cached is None or cached_timeout != query_timeout:
        cached = get_la_client(timeout=(10, query_timeout))
        _THREAD_LOCAL.la_client = cached
        _THREAD_LOCAL.query_timeout = query_timeout
    return cached


def _run_query(la, namespace, query, start, end, timeout=None):
    import oci

    try:
        deadline = query_deadline(timeout) if threading.current_thread() is threading.main_thread() \
            else nullcontext()
        with deadline:
            result = la.query(
                namespace_name=namespace,
                query_details=oci.log_analytics.models.QueryDetails(
                    compartment_id=COMPARTMENT_ID,
                    compartment_id_in_subtree=True,
                    query_string=query,
                    sub_system="LOG",
                    max_total_count=10,
                    time_filter=oci.log_analytics.models.TimeRange(
                        time_start=start, time_end=end, time_zone="UTC",
                    ),
                ),
            )
        return len(getattr(result.data, "items", []) or []), None
    except Exception as exc:  # noqa: BLE001
        return -1, redact_text(str(exc))


def _status_for_widget(row_count: int, error: str | None, visualization_type: str) -> str:
    if error:
        return "ERROR"
    if row_count > 0 or visualization_type == "link":
        return "HIT"
    return "MISS"


def _verify_widget_task(task, namespace, start, end, query_timeout):
    la = _get_thread_la_client(query_timeout)
    count, err = _run_query(
        la,
        namespace,
        task["query_string"],
        start,
        end,
        timeout=query_timeout,
    )
    status = _status_for_widget(count, err, task["visualization_type"])
    return WidgetVerification(
        task["dashboard"],
        task["widget"],
        max(count, 0),
        status,
        err,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify redeployed SOC dashboards")
    parser.add_argument("--lookback", default="21d")
    parser.add_argument("--query-timeout", type=int, default=60,
                        help="Per-widget OCI query timeout in seconds")
    parser.add_argument("--max-workers", type=int, default=1,
                        help="Parallel OCI query workers. Default keeps serial behavior.")
    parser.add_argument("--json", help="JSON report path")
    parser.add_argument("--dashboard-name", action="append", dest="dashboard_names",
                        help="Verify only the named dashboard. Can be supplied multiple times.")
    args = parser.parse_args()

    try:
        dashboards_to_verify = select_dashboards(args.dashboard_names)
    except ValueError as exc:
        print(exc)
        return 2

    require_oci_config()
    md = get_dashboard_client()
    la = get_la_client(timeout=(10, args.query_timeout))
    namespace = LA_NAMESPACE
    if not namespace:
        ns = la.list_namespaces(compartment_id=TENANCY_ID).data.items
        namespace = ns[0].namespace_name

    end = datetime.now(timezone.utc)
    start = end - _parse_lookback(args.lookback)

    dashboard_records = []
    widget_records: list[WidgetVerification] = []
    widget_tasks = []
    total_widgets = sum(len(cfg["widgets"]) for cfg in dashboards_to_verify.values())
    widget_index = 0

    for name, cfg in dashboards_to_verify.items():
        expected_count = len(cfg["widgets"])
        try:
            resp = md.list_management_dashboards(
                compartment_id=COMPARTMENT_ID, display_name=name, limit=5,
            )
            items = resp.data.items
        except Exception as exc:  # noqa: BLE001
            dashboard_records.append({
                "name": name, "exists": False, "error": redact_text(str(exc))[:120],
            })
            continue

        if not items:
            dashboard_records.append({
                "name": name, "exists": False, "expected_widgets": expected_count,
            })
            continue

        d = items[0]
        try:
            full = md.get_management_dashboard(d.dashboard_id).data
            saved_searches = full.saved_searches or []
        except Exception as exc:  # noqa: BLE001
            dashboard_records.append({
                "name": name, "exists": True, "error": redact_text(str(exc))[:120],
            })
            continue

        actual_count = len(full.tiles or [])
        dashboard_records.append({
            "name": name,
            "exists": True,
            "expected_widgets": expected_count,
            "actual_widgets": actual_count,
            "saved_search_count": len(saved_searches),
            "match": actual_count == expected_count,
            "dashboard_id": d.dashboard_id,
        })

        for ss in saved_searches:
            ui_config = ss.ui_config if isinstance(ss.ui_config, dict) \
                else getattr(ss, "ui_config", {}) or {}
            query_string = ui_config.get("queryString") if isinstance(ui_config, dict) \
                else None
            if not query_string:
                widget_records.append(WidgetVerification(
                    name, ss.display_name, 0, "ERROR",
                    "no queryString in saved search ui_config"))
                continue
            widget_index += 1
            viz = ui_config.get("visualizationType", "table") if isinstance(ui_config, dict) \
                else "table"
            widget_tasks.append({
                "index": widget_index,
                "dashboard": name,
                "widget": ss.display_name,
                "query_string": query_string,
                "visualization_type": viz,
            })

    worker_count = max(1, args.max_workers)
    if worker_count == 1:
        for task in widget_tasks:
            print(
                f"  [{task['index']:03d}/{total_widgets}] "
                f"{task['dashboard']} :: {task['widget']}",
                flush=True,
            )
            widget_records.append(
                _verify_widget_task(task, namespace, start, end, args.query_timeout)
            )
    else:
        print(f"  Running widget queries with {worker_count} workers...", flush=True)
        results_by_index = {}
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            future_map = {}
            for task in widget_tasks:
                print(
                    f"  [{task['index']:03d}/{total_widgets}] "
                    f"{task['dashboard']} :: {task['widget']}",
                    flush=True,
                )
                future = executor.submit(
                    _verify_widget_task,
                    task,
                    namespace,
                    start,
                    end,
                    args.query_timeout,
                )
                future_map[future] = task

            for future in as_completed(future_map):
                task = future_map[future]
                try:
                    results_by_index[task["index"]] = future.result()
                except Exception as exc:  # noqa: BLE001
                    results_by_index[task["index"]] = WidgetVerification(
                        task["dashboard"],
                        task["widget"],
                        0,
                        "ERROR",
                        redact_text(str(exc)),
                    )

        for index in sorted(results_by_index):
            widget_records.append(results_by_index[index])

    print("=" * 78)
    print("Dashboard Health Verification")
    print("=" * 78)
    missing = [d for d in dashboard_records if not d.get("exists")]
    mismatched = [d for d in dashboard_records if d.get("exists") and not d.get("match", True)]
    print(f"Total expected dashboards: {len(dashboards_to_verify)}")
    print(f"Missing dashboards:        {len(missing)}")
    print(f"Widget-count mismatch:     {len(mismatched)}")
    if missing:
        print("\nMissing dashboards:")
        for d in missing:
            print(f"  - {d['name']}")
    if mismatched:
        print("\nMismatched widget counts:")
        for d in mismatched:
            print(f"  - {d['name']}: expected={d['expected_widgets']}  actual={d['actual_widgets']}")

    print()
    print("Per-dashboard widget HIT/MISS/ERROR:")
    by_dash: dict[str, Counter] = defaultdict(Counter)
    for w in widget_records:
        by_dash[w.dashboard][w.status] += 1
    for d in sorted(by_dash):
        c = by_dash[d]
        total = sum(c.values())
        print(f"  {d:55s}  HIT={c.get('HIT',0):>2d}  "
              f"MISS={c.get('MISS',0):>2d}  ERR={c.get('ERROR',0):>2d}  "
              f"({total} widgets)")

    totals = Counter(w.status for w in widget_records)
    print("-" * 78)
    print(f"{'OVERALL':57s}  HIT={totals.get('HIT',0):>2d}  "
          f"MISS={totals.get('MISS',0):>2d}  ERR={totals.get('ERROR',0):>2d}  "
          f"({sum(totals.values())} widgets)")

    if args.json:
        Path(args.json).write_text(json.dumps({
            "dashboards": dashboard_records,
            "widgets": [asdict(w) for w in widget_records],
        }, indent=2), encoding="utf-8")
        print(f"\nJSON report written to: {args.json}")

    if missing or any(w.status == "ERROR" for w in widget_records):
        return 2
    if any(w.status == "MISS" for w in widget_records) or mismatched:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
