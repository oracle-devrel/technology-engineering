"""Human-facing stdout reporting for the dashboard deploy CLI.

These printers are the deploy command's UX/test contract (the ✅/plan/summary
text consumed by pipelines and asserted by tests). They are extracted from
``scripts/deploy_dashboard.py`` so the orchestrator stays under the module-size
ceiling; behavior is unchanged — same strings, same stdout stream.
"""

from __future__ import annotations

from typing import Any, Mapping


def print_dry_run_plan(inventory: Mapping[str, Any]) -> None:
    """Print the ``--dry-run`` deployment plan for an inventory (no side effects)."""
    print("\n  [DRY RUN] No changes will be made.\n")
    for dashboard in inventory["dashboards"]:
        print(f"  Dashboard: {dashboard['name']}")
        print(f"    Widgets: {dashboard['widget_count']}")
        for widget in dashboard["widgets"]:
            print(
                f"      - {widget['title']} ({widget['query_file']}) "
                f"[viz={widget['visualization_type']}]"
            )
    print(
        f"\n  Total: {inventory['summary']['total_dashboards']} dashboards, "
        f"{inventory['summary']['total_widgets']} saved searches"
    )


def print_deployment_summary(total_searches: int, total_dashboards: int) -> None:
    """Print the post-deploy summary banner."""
    print(f"\n{'=' * 60}")
    print("Deployment Summary")
    print(f"{'=' * 60}")
    print(f"  Saved Searches created/found: {total_searches}")
    print(f"  Dashboards imported: {total_dashboards}")
    print(f"\n  View in OCI Console:")
    print(f"  Observability & Management > Log Analytics > Dashboards")
