#!/usr/bin/env python3
"""Inventory every Management Dashboard in the SOC compartment.

Lists every dashboard, classifies it as ``SOC`` (matches the names produced
by ``deploy_dashboard.py``) or ``other``, counts embedded saved searches per
dashboard, and flags duplicates so cleanup is safe.

Usage:
    python3 scripts/inventory_dashboards.py [--json out.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "scripts"))

from deploy_dashboard import DASHBOARDS  # noqa: E402
from oci_config import COMPARTMENT_ID, get_dashboard_client  # noqa: E402


def _list_all_dashboards(md_client):
    items = []
    page = None
    while True:
        kwargs = {"compartment_id": COMPARTMENT_ID, "limit": 100}
        if page:
            kwargs["page"] = page
        resp = md_client.list_management_dashboards(**kwargs)
        items.extend(resp.data.items or [])
        page = resp.headers.get("opc-next-page")
        if not page:
            break
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventory SOC dashboards")
    parser.add_argument("--json", help="Write machine-readable JSON report")
    args = parser.parse_args()

    md = get_dashboard_client()
    items = _list_all_dashboards(md)

    by_name: dict[str, list] = defaultdict(list)
    for d in items:
        by_name[d.display_name].append(d)

    expected = set(DASHBOARDS.keys())

    soc_records = []
    other_count = 0
    for name, instances in sorted(by_name.items()):
        is_soc = name.startswith("SOC") or name in expected
        for d in instances:
            try:
                full = md.get_management_dashboard(d.dashboard_id).data
                widget_count = len(full.tiles or [])
                ss_count = len(full.saved_searches or [])
            except Exception:  # noqa: BLE001
                widget_count = 0
                ss_count = 0
            record = {
                "id": d.id,
                "dashboard_id": d.dashboard_id,
                "display_name": name,
                "is_soc": is_soc,
                "is_expected": name in expected,
                "is_duplicate": len(instances) > 1,
                "widget_count": widget_count,
                "saved_search_count": ss_count,
                "lifecycle_state": getattr(d, "lifecycle_state", None),
                "time_created": str(getattr(d, "time_created", "")),
            }
            if is_soc:
                soc_records.append(record)
            else:
                other_count += 1

    expected_present = {r["display_name"] for r in soc_records if r["is_expected"]}
    expected_missing = sorted(expected - expected_present)
    duplicates = [r for r in soc_records if r["is_duplicate"]]
    legacy = [r for r in soc_records if not r["is_expected"]]
    broken = [r for r in soc_records if r["widget_count"] == 0]

    print("=" * 70)
    print("SOC Dashboard Inventory")
    print("=" * 70)
    print(f"Total dashboards in compartment:  {len(items)}")
    print(f"  SOC dashboards:                 {len(soc_records)}")
    print(f"  Non-SOC dashboards:             {other_count}")
    print(f"  Expected (in DASHBOARDS):       {len(expected)}")
    print(f"  Expected present:               {len(expected_present)}")
    print(f"  Expected missing:               {len(expected_missing)}")
    print(f"  Duplicate SOC names:            {len(duplicates)}")
    print(f"  Legacy SOC (not in DASHBOARDS): {len(legacy)}")
    print(f"  Broken (zero widgets):          {len(broken)}")
    print()
    if expected_missing:
        print("Missing expected dashboards:")
        for n in expected_missing:
            print(f"  - {n}")
        print()
    if duplicates:
        print("Duplicates:")
        seen = set()
        for r in duplicates:
            key = r["display_name"]
            if key in seen:
                continue
            seen.add(key)
            print(f"  {key}: "
                  f"{sum(1 for d in soc_records if d['display_name'] == key)} copies")
        print()
    if legacy:
        print("Legacy SOC dashboards (not in current DASHBOARDS map):")
        for r in legacy:
            print(f"  {r['display_name']}  widgets={r['widget_count']}  "
                  f"id={r['dashboard_id']}")
        print()
    if broken:
        print("Broken (zero-widget) SOC dashboards:")
        for r in broken:
            print(f"  {r['display_name']}  id={r['dashboard_id']}  "
                  f"created={r['time_created'][:10]}")
        print()

    print("Per-dashboard widget/saved-search counts:")
    for r in sorted(soc_records, key=lambda r: r["display_name"]):
        flag = ""
        if r["is_duplicate"]:
            flag += " [DUP]"
        if not r["is_expected"]:
            flag += " [LEGACY]"
        if r["widget_count"] == 0:
            flag += " [BROKEN]"
        print(f"  {r['display_name']:55s} widgets={r['widget_count']:>2d} "
              f"saved={r['saved_search_count']:>2d}{flag}")

    if args.json:
        report = {
            "summary": {
                "total": len(items),
                "soc": len(soc_records),
                "other": other_count,
                "expected_total": len(expected),
                "expected_present": len(expected_present),
                "expected_missing": expected_missing,
                "duplicates": len(duplicates),
                "legacy": len(legacy),
                "broken": len(broken),
            },
            "soc_dashboards": soc_records,
        }
        Path(args.json).write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\nJSON report: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
