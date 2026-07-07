#!/usr/bin/env python3
"""Aggressively delete every SOC-named Management Dashboard and saved search.

This cleanup is more thorough than ``deploy_dashboard.py --cleanup``:

- Deletes any dashboard whose ``displayName`` starts with ``SOC`` or matches
  the ``OCI-DEMO`` showcase prefix, not only the names currently listed in
  ``deploy_dashboard.DASHBOARDS``. That catches stale entries from prior
  iterations whose titles drifted.
- Deletes every saved search whose title appears in the current
  ``DASHBOARDS`` widget list AND any orphan saved searches whose title
  begins with the SOC widget prefixes (``SOC:``, ``OCI:``, ``STIG:``,
  ``CG:``, ``Hunt:``, ``Browser:``, ``APM:``, ``YARA:``, ``APT37:``,
  ``BLUELIGHT:``, ``Geo:``).

Use only when you intend to fully rebuild SOC content.

Usage:
    python3 scripts/cleanup_soc_dashboards.py [--dry-run]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "scripts"))

from deploy_dashboard import DASHBOARDS  # noqa: E402
from oci_config import COMPARTMENT_ID, get_dashboard_client  # noqa: E402

SOC_DASHBOARD_PREFIXES = (
    "SOC ",
    "SOC:",
    "OCI-DEMO:",
)
SOC_WIDGET_PREFIXES = (
    "SOC:", "OCI:", "STIG:", "CG:", "Hunt:", "Browser:", "APM:",
    "YARA:", "APT37:", "BLUELIGHT:", "Geo:", "OCI-DEMO:",
)


def _list_all_dashboards(md):
    items = []
    page = None
    while True:
        kwargs = {"compartment_id": COMPARTMENT_ID, "limit": 100}
        if page:
            kwargs["page"] = page
        resp = md.list_management_dashboards(**kwargs)
        items.extend(resp.data.items or [])
        page = resp.headers.get("opc-next-page")
        if not page:
            break
    return items


def _list_all_saved_searches(md):
    items = []
    page = None
    while True:
        kwargs = {"compartment_id": COMPARTMENT_ID, "limit": 100}
        if page:
            kwargs["page"] = page
        resp = md.list_management_saved_searches(**kwargs)
        items.extend(resp.data.items or [])
        page = resp.headers.get("opc-next-page")
        if not page:
            break
    return items


def cleanup(dry_run: bool) -> None:
    md = get_dashboard_client()

    expected_names = set(DASHBOARDS.keys())
    dashboards = _list_all_dashboards(md)
    soc_dashboards = [
        d for d in dashboards
        if d.display_name in expected_names
        or d.display_name.startswith(SOC_DASHBOARD_PREFIXES)
    ]
    print(f"Dashboards in compartment: {len(dashboards)}")
    print(f"  SOC dashboards to delete: {len(soc_dashboards)}")
    for d in soc_dashboards:
        print(f"    - {d.display_name}  ({d.dashboard_id})")
    if not dry_run:
        for d in soc_dashboards:
            try:
                md.delete_management_dashboard(d.dashboard_id)
                print(f"    deleted: {d.display_name}")
            except Exception as exc:  # noqa: BLE001
                print(f"    ERR    : {d.display_name}: {str(exc)[:120]}")

    expected_widget_titles = set()
    for cfg in DASHBOARDS.values():
        for w in cfg["widgets"]:
            expected_widget_titles.add(w["title"])

    saved = _list_all_saved_searches(md)
    soc_saved = [
        s for s in saved
        if s.display_name in expected_widget_titles
        or s.display_name.startswith(SOC_WIDGET_PREFIXES)
    ]
    print(f"\nSaved searches in compartment: {len(saved)}")
    print(f"  SOC saved searches to delete: {len(soc_saved)}")
    if not dry_run:
        for s in soc_saved:
            try:
                md.delete_management_saved_search(s.id)
            except Exception as exc:  # noqa: BLE001
                print(f"    ERR  {s.display_name}: {str(exc)[:120]}")
        print(f"  deleted {len(soc_saved)} saved searches")
    else:
        for s in soc_saved[:20]:
            print(f"    - {s.display_name}")
        if len(soc_saved) > 20:
            print(f"    ... +{len(soc_saved) - 20} more")


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggressively cleanup SOC dashboards")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be deleted without executing")
    args = parser.parse_args()
    cleanup(args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
