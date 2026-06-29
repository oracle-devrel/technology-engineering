#!/usr/bin/env python3
"""Run every detection / hunting / app query against live OCI Log Analytics.

Walks runnable query JSON under ``queries/**`` (excluding generated inventory
artifacts such as ``manifest.json``, ``catalog.json``, and field/spec exports),
strips post-pipeline aggregations for the smoke check (so the runner counts
matching raw rows even when the original widget query ends in ``stats``),
and reports HIT / MISS / ERROR per query plus a per-directory rollup.

Usage:
    python3 scripts/smoke_test_all_queries.py [--lookback 21d] [--json out.json]
                                              [--include-aggregations] [--limit 10]

Exit codes:
    0 = every query returned at least one row (HIT)
    1 = at least one query returned zero rows (MISS) — silent-zero risk
    2 = at least one query failed (ERROR)
    3 = OCI auth / namespace lookup failed
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "scripts"))

from oci_config import (  # noqa: E402
    COMPARTMENT_ID,
    LA_NAMESPACE,
    TENANCY_ID,
    get_la_client,
    require_oci_config,
)
from query_artifacts import is_saved_search_query_file  # noqa: E402

QUERIES_DIR = PROJECT_DIR / "queries"


@dataclass(frozen=True)
class QueryResult:
    relative_path: str
    title: str
    category: str  # "detection" | "app" | "hunting"
    row_count: int
    status: str  # HIT | MISS | ERROR
    error: str | None = None


def _parse_lookback(value: str) -> timedelta:
    units = {"m": "minutes", "h": "hours", "d": "days"}
    if not value or value[-1] not in units:
        raise ValueError(f"Invalid lookback '{value}'. Use forms like 60m, 6h, 30d.")
    return timedelta(**{units[value[-1]]: int(value[:-1])})


def _time_window(lookback: str) -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    return now - _parse_lookback(lookback), now


def _strip_aggregations(query: str) -> str:
    """Return the raw filter half of a query (everything before the first ``|``).

    The pipe must be at the OCL command level — pipes inside ``like '...'``
    literals (e.g. ``msg like '*| nc *'`` for shell-pipe payloads) are part
    of the search value, not stage delimiters. Splitting naively on the
    first ``|`` truncates the literal and produces ``Invalid string for
    LIKE: '`` errors during smoke tests.
    """
    in_quote = False
    for i, ch in enumerate(query):
        if ch == "'":
            in_quote = not in_quote
        elif ch == "|" and not in_quote:
            return query[:i].strip()
    return query.strip()


def _classify(rel_path: str) -> str:
    if rel_path.startswith("apps/"):
        return "app"
    if rel_path.startswith("hunting/"):
        return "hunting"
    return "detection"


def _iter_query_files() -> Iterable[Path]:
    for path in sorted(QUERIES_DIR.rglob("*.json")):
        if not is_saved_search_query_file(path):
            continue
        yield path


def _run_query(la_client, namespace, query, start, end, limit):
    import oci

    try:
        result = la_client.query(
            namespace_name=namespace,
            query_details=oci.log_analytics.models.QueryDetails(
                compartment_id=COMPARTMENT_ID,
                query_string=query,
                sub_system="LOG",
                max_total_count=limit,
                time_filter=oci.log_analytics.models.TimeRange(
                    time_start=start,
                    time_end=end,
                    time_zone="UTC",
                ),
            ),
        )
        items = getattr(result.data, "items", []) or []
        return len(items), None
    except Exception as exc:  # noqa: BLE001
        return -1, str(exc)


def smoke_test(lookback: str, include_aggregations: bool, limit: int) -> list[QueryResult]:
    require_oci_config()
    la_client = get_la_client()
    namespace = LA_NAMESPACE
    if not namespace:
        ns_resp = la_client.list_namespaces(compartment_id=TENANCY_ID).data
        if not ns_resp.items:
            raise RuntimeError("No Log Analytics namespace found in tenancy.")
        namespace = ns_resp.items[0].namespace_name

    start, end = _time_window(lookback)
    out: list[QueryResult] = []
    for path in _iter_query_files():
        rel = path.relative_to(QUERIES_DIR).as_posix()
        try:
            spec = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            out.append(QueryResult(rel, path.name, _classify(rel), 0,
                                   "ERROR", f"json parse: {exc}"))
            continue
        title = spec.get("title", path.name)
        raw_query = spec.get("query")
        if not raw_query:
            out.append(QueryResult(rel, title, _classify(rel), 0,
                                   "ERROR", "missing query field"))
            continue
        query_to_run = raw_query if include_aggregations else _strip_aggregations(raw_query)
        count, err = _run_query(la_client, namespace, query_to_run, start, end, limit)
        # ``link`` widget queries store grouping in side-channel structures;
        # treat any non-error response as HIT for those.
        viz = (spec.get("dashboard") or {}).get("visualizationType", "")
        if err:
            status = "ERROR"
        elif count > 0 or (include_aggregations and viz == "link"):
            status = "HIT"
        else:
            status = "MISS"
        out.append(QueryResult(rel, title, _classify(rel),
                               max(count, 0), status, err))
    return out


def _print_rollup(results: list[QueryResult]) -> None:
    totals = Counter(r.status for r in results)
    by_category: dict[str, Counter] = defaultdict(Counter)
    for r in results:
        by_category[r.category][r.status] += 1

    print("\n=== Per-category rollup ===")
    print(f"{'CATEGORY':12s} {'HIT':>5s} {'MISS':>5s} {'ERROR':>6s} {'TOTAL':>6s}")
    print("-" * 40)
    for category in sorted(by_category):
        c = by_category[category]
        total = sum(c.values())
        print(f"{category:12s} {c.get('HIT',0):>5d} {c.get('MISS',0):>5d} "
              f"{c.get('ERROR',0):>6d} {total:>6d}")
    print("-" * 40)
    print(f"{'OVERALL':12s} {totals.get('HIT',0):>5d} {totals.get('MISS',0):>5d} "
          f"{totals.get('ERROR',0):>6d} {sum(totals.values()):>6d}")


def _print_problems(results: list[QueryResult]) -> None:
    misses = [r for r in results if r.status == "MISS"]
    errors = [r for r in results if r.status == "ERROR"]
    if errors:
        print(f"\n=== {len(errors)} ERROR queries ===")
        for r in errors:
            print(f"  {r.relative_path}")
            if r.error:
                print(f"    -> {r.error[:160]}")
    if misses:
        print(f"\n=== {len(misses)} MISS queries (zero rows) ===")
        for r in misses:
            print(f"  {r.relative_path}  ({r.title[:60]})")


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test all detection queries")
    parser.add_argument("--lookback", default="21d",
                        help="Lookback window (e.g. 60m, 6h, 21d). Default: 21d")
    parser.add_argument("--include-aggregations", action="store_true",
                        help="Run the full pipelined query instead of only the filter half")
    parser.add_argument("--limit", type=int, default=10,
                        help="max_total_count per query. Default: 10")
    parser.add_argument("--json", help="Write machine-readable JSON report to this path")
    args = parser.parse_args()

    try:
        results = smoke_test(args.lookback, args.include_aggregations, args.limit)
    except Exception as exc:  # noqa: BLE001
        print(f"FATAL: {exc}", file=sys.stderr)
        return 3

    _print_rollup(results)
    _print_problems(results)

    if args.json:
        Path(args.json).write_text(
            json.dumps([asdict(r) for r in results], indent=2),
            encoding="utf-8",
        )
        print(f"\nJSON report written to {args.json}")

    statuses = {r.status for r in results}
    if "ERROR" in statuses:
        return 2
    if "MISS" in statuses:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
