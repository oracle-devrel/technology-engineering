"""
Deploy SOC detection dashboards to OCI Log Analytics.

Creates 22 dashboards backed by 343 embedded saved-search widgets covering:
  - OCI audit and STIG compliance
  - Cloud Guard, Linux, Windows, Sysmon network, and web detections
  - Browser/APM detections, application analytics, APT content, and hunting
  - FreeLabFriday-inspired C2/exfiltration/persistence hunts
  - 2025-2026 MELTS hunts for ClickFix, ToolShell, RMM, token replay, and exfiltration
  - Geographic health / multicloud operational views

Usage:
  python3 scripts/deploy_dashboard.py              # Deploy all
  python3 scripts/deploy_dashboard.py --cleanup     # Delete existing SOC content first
  python3 scripts/deploy_dashboard.py --dashboard-name "C2 & Beaconing Detection"
  python3 scripts/deploy_dashboard.py --dry-run     # Print plan without executing
  python3 scripts/deploy_dashboard.py --export-inventory
"""

import json
import os
import sys
import argparse
import time
from collections import Counter
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oci_config import (
    TENANCY_ID, COMPARTMENT_ID, QUERIES_DIR, HUNTING_DIR, LA_NAMESPACE,
    get_dashboard_client, get_la_client, get_namespace, validate_oci_setup,
    assert_write_allowed, ProdWriteGuardError,
)

import oci

# ─── Extracted modules ───────────────────────────────────────────
# Re-exported so existing ``from deploy_dashboard import X`` call sites keep working.
from dashboards.catalog import (
    DASHBOARDS,
    select_dashboards,
    octo_apm_workshop_widget,
    load_sentinel_dashboard_groups,
    SENTINEL_DASHBOARD_GROUPS,
    SENTINEL_DASHBOARD_DESCRIPTIONS,
    SENTINEL_LIVE_VALIDATION_PASS_VALUES,
    SENTINEL_DASHBOARD_UNSUPPORTED_QUERY_PATTERNS,
)
from dashboards.builders import (
    SUPPORTED_VISUALIZATION_TYPES,
    ADVANCED_VISUALIZATION_TYPES,
    FIELD_REFERENCE_RE,
    FIELD_OPERATOR_RE,
    DEFAULT_DASHBOARD_TIME_PERIOD,
    DASHBOARD_GRID_COLUMNS,
    VISUALIZATION_LAYOUT_DEFAULTS,
    load_query_info,
    extract_dashboard_query_fields,
    build_widget_drilldowns,
    score_dashboard_widget_quality,
    build_scope_filters,
    resolve_widget_ui_config,
    build_saved_search_json,
    iter_inventory_widgets,
    _iter_quoted_values,
    _resolve_ask_ai_prompts,
    _quote_context_indicates_field,
    _coerce_layout_dimension,
)
from dashboards.validation import (
    PROGRESS_REDACTIONS,
    DEFAULT_QUERY_VALIDATION_LOOKBACK,
    query_deadline,
    validate_query_in_oci,
    validate_query_in_oci_isolated,
    resolve_validation_namespace,
    _validate_query_worker,
    _redact_progress_text,
    _validation_status,
    _should_emit_validation_progress,
    _format_validation_progress,
)
from dashboards.reporting import print_dry_run_plan, print_deployment_summary
from obs_logging import get_logger, bind

# Structured diagnostics → stderr (run-id correlated). The ✅/❌ stdout prints
# below remain the human/pipeline-facing UX contract; these log lines are an
# additive, machine-parseable record of the live-OCI lifecycle and failures.
log = get_logger("deploy_dashboard")

DASHBOARD_INVENTORY_PATH = os.path.join(QUERIES_DIR, "dashboard_inventory.json")


def _build_widget_inventory_record(dashboard_name, dashboard_index, widget, widget_index, queries_dir):
    query_info = load_query_info(widget["query_file"], queries_dir=queries_dir)
    ui_config = resolve_widget_ui_config(widget, query_info)
    layout = resolve_widget_layout(widget, query_info)

    return {
        "dashboard_name": dashboard_name,
        "dashboard_index": dashboard_index,
        "widget_index": widget_index,
        "title": widget["title"],
        "query_file": widget["query_file"],
        "query_title": query_info["title"],
        "description": query_info.get("description", ""),
        "level": query_info.get("level", ""),
        "type": query_info.get("type", "detection" if query_info.get("sigma_id") else "curated"),
        "sigma_id": query_info.get("sigma_id", ""),
        "tags": query_info.get("tags", []),
        "references": query_info.get("references", []),
        "logsource": query_info.get("logsource", {}),
        "mitre_attack": query_info.get("mitre_attack", {}),
        "visualization_type": ui_config["visualizationType"],
        "visualization_options": ui_config.get("visualizationOptions", {}),
        "time_selection": ui_config.get("timeSelection", {}),
        "layout": layout,
        "ask_ai_prompts": _resolve_ask_ai_prompts(widget, query_info),
        "advanced_visualization": ui_config["visualizationType"] in ADVANCED_VISUALIZATION_TYPES,
        "drilldowns": build_widget_drilldowns(query_info),
        "dashboard_quality": score_dashboard_widget_quality(ui_config, layout),
    }


def build_dashboard_inventory(dashboards=None, queries_dir=QUERIES_DIR, generated_at=None):
    """Build a dashboard/widget inventory artifact from ``DASHBOARDS``.

    The resulting JSON is the dashboard-facing contract. It lets downstream UI
    code consume dashboard/widget/query metadata without importing or parsing
    this Python deployment script at runtime.
    """
    dashboards = dashboards or DASHBOARDS
    generated_at = generated_at or datetime.now(timezone.utc).isoformat()

    dashboard_records = []
    visualization_counts = Counter()
    level_counts = Counter()
    total_widgets = 0

    for dashboard_index, (dashboard_name, config) in enumerate(dashboards.items()):
        widget_records = []
        for widget_index, widget in enumerate(config["widgets"]):
            record = _build_widget_inventory_record(
                dashboard_name=dashboard_name,
                dashboard_index=dashboard_index,
                widget=widget,
                widget_index=widget_index,
                queries_dir=queries_dir,
            )
            widget_records.append(record)
            visualization_counts[record["visualization_type"]] += 1
            if record["level"]:
                level_counts[record["level"]] += 1

        total_widgets += len(widget_records)
        dashboard_records.append({
            "name": dashboard_name,
            "description": config.get("description", ""),
            "widget_count": len(widget_records),
            "widgets": widget_records,
        })

    return {
        "version": "1.0",
        "generated_at": generated_at,
        "source": "scripts/deploy_dashboard.py:DASHBOARDS",
        "summary": {
            "total_dashboards": len(dashboard_records),
            "total_widgets": total_widgets,
            "advanced_visualization_widgets": sum(
                count for viz, count in visualization_counts.items()
                if viz in ADVANCED_VISUALIZATION_TYPES
            ),
            "visualization_types": dict(sorted(visualization_counts.items())),
            "levels": dict(sorted(level_counts.items())),
        },
        "dashboards": dashboard_records,
    }


def _resolve_inventory_source_widget(dashboard_name, inventory_widget):
    """Find the source DASHBOARDS widget for an inventory widget."""
    dashboard_config = DASHBOARDS.get(dashboard_name, {})
    source_widgets = dashboard_config.get("widgets", [])
    widget_index = inventory_widget.get("widget_index")
    query_file = inventory_widget.get("query_file")

    if isinstance(widget_index, int) and 0 <= widget_index < len(source_widgets):
        source_widget = source_widgets[widget_index]
        if source_widget.get("query_file") == query_file:
            return source_widget

    for source_widget in source_widgets:
        if (
            source_widget.get("query_file") == query_file
            and source_widget.get("title") == inventory_widget.get("title")
        ):
            return source_widget

    return inventory_widget


def validate_dashboard_inventory(inventory, queries_dir=QUERIES_DIR):
    """Validate that an inventory artifact still matches query metadata."""
    errors = []
    dashboards = inventory.get("dashboards", [])

    summary = inventory.get("summary", {})
    expected_dashboard_count = len(dashboards)
    actual_widget_count = sum(len(dashboard.get("widgets", [])) for dashboard in dashboards)

    if summary.get("total_dashboards") != expected_dashboard_count:
        errors.append(
            f"summary.total_dashboards mismatch: "
            f"{summary.get('total_dashboards')} != {expected_dashboard_count}"
        )
    if summary.get("total_widgets") != actual_widget_count:
        errors.append(
            f"summary.total_widgets mismatch: "
            f"{summary.get('total_widgets')} != {actual_widget_count}"
        )

    for dashboard in dashboards:
        dashboard_name = dashboard.get("name", "<unknown dashboard>")
        widgets = dashboard.get("widgets", [])
        if dashboard.get("widget_count") != len(widgets):
            errors.append(f"{dashboard_name}: widget_count mismatch")

        for widget in widgets:
            query_file = widget.get("query_file", "")
            label = f"{dashboard_name} / {query_file}"
            try:
                query_info = load_query_info(query_file, queries_dir=queries_dir)
                source_widget = _resolve_inventory_source_widget(dashboard_name, widget)
                ui_config = resolve_widget_ui_config(source_widget, query_info)
            except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
                errors.append(f"{label}: {exc}")
                continue

            if widget.get("query_title") != query_info.get("title"):
                errors.append(
                    f"{label}: query_title mismatch "
                    f"({widget.get('query_title')!r} != {query_info.get('title')!r})"
                )

            if widget.get("references", []) != query_info.get("references", []):
                errors.append(f"{label}: references mismatch")

            expected_viz = ui_config["visualizationType"]
            if widget.get("visualization_type") != expected_viz:
                errors.append(
                    f"{label}: visualization_type mismatch "
                    f"({widget.get('visualization_type')!r} != {expected_viz!r})"
                )

            expected_layout = resolve_widget_layout(source_widget, query_info)
            if widget.get("layout") != expected_layout:
                errors.append(
                    f"{label}: layout mismatch "
                    f"({widget.get('layout')!r} != {expected_layout!r})"
                )

    return errors


def write_dashboard_inventory(path=DASHBOARD_INVENTORY_PATH, inventory=None):
    """Write the generated dashboard inventory artifact to disk."""
    inventory = inventory or build_dashboard_inventory()
    errors = validate_dashboard_inventory(inventory)
    if errors:
        raise ValueError("dashboard inventory validation failed:\n" + "\n".join(errors))

    with open(path, "w") as f:
        json.dump(inventory, f, indent=2)
        f.write("\n")

    return path


def resolve_widget_layout(widget, query_info):
    """Return OCI dashboard tile dimensions for one widget.

    Wide result sets are the default in this repository, so table-like
    visualizations receive full-width tiles unless explicitly overridden.
    """
    dashboard_meta = query_info.get("dashboard", {}) if isinstance(query_info, dict) else {}
    visualization_type = resolve_widget_ui_config(widget, query_info)["visualizationType"]
    layout = VISUALIZATION_LAYOUT_DEFAULTS.get(visualization_type, {"width": 12, "height": 5}).copy()

    metadata_layout = dashboard_meta.get("layout", {})
    if isinstance(metadata_layout, dict):
        layout.update(metadata_layout)

    widget_layout = widget.get("layout", {})
    if isinstance(widget_layout, dict):
        layout.update(widget_layout)

    width = _coerce_layout_dimension(
        layout.get("width"),
        VISUALIZATION_LAYOUT_DEFAULTS.get(visualization_type, {}).get("width", 12),
        lower_bound=1,
        upper_bound=DASHBOARD_GRID_COLUMNS,
    )
    height = _coerce_layout_dimension(
        layout.get("height"),
        VISUALIZATION_LAYOUT_DEFAULTS.get(visualization_type, {}).get("height", 5),
        lower_bound=1,
    )
    return {"width": width, "height": height}


def build_dashboard_json(dashboard_id, name, description, widgets, widget_queries):
    """Build a complete dashboard JSON with embedded saved searches.

    The import_dashboard API requires both tiles and their saved search
    definitions in a single JSON. Tiles reference saved searches by short
    'id' fields, not OCIDs.
    """
    tiles = []
    saved_searches = []
    current_row = 0
    current_column = 0
    current_row_height = 0

    # Per-deploy unique suffix taken from the timestamped dashboard_id
    # (``soc-<slug>-<ts>``). Embedded saved-search IDs must be unique per deploy:
    # a stable filename-based ID collides with OCI's *soft-deleted* saved search
    # of the same ID when --cleanup ran first, and the import resurrects the old
    # saved search (stale visualizationType / timeSelection) instead of applying
    # the new uiConfig. The tile's savedSearchId uses the same suffixed ID, so the
    # in-import reference stays consistent.
    deploy_suffix = dashboard_id.rsplit('-', 1)[-1]

    for i, (widget, query_info) in enumerate(zip(widgets, widget_queries)):
        if query_info is None:
            continue

        # Unique-per-deploy short ID from the query filename + deploy suffix.
        search_id = (
            widget['query_file'].replace('.json', '').replace('_', '-')
            + '-' + deploy_suffix
        )

        layout = resolve_widget_layout(widget, query_info)
        width = layout["width"]
        height = layout["height"]

        if current_column and current_column + width > DASHBOARD_GRID_COLUMNS:
            current_row += current_row_height
            current_column = 0
            current_row_height = 0

        row = current_row
        col = current_column

        # Build the tile referencing the saved search by short ID
        tiles.append({
            "displayName": widget['title'],
            "savedSearchId": search_id,
            "row": row,
            "column": col,
            "height": height,
            "width": width,
            "nls": {},
            "uiConfig": {},
            "dataConfig": [],
            "state": "DEFAULT",
            "drilldownConfig": [],
            "parametersMap": {
                "log-analytics-entity": "$(dashboard.params.log-analytics-entity-filter)",
                "log-analytics-log-group-compartment": "$(dashboard.params.log-analytics-loggroup-filter)",
                "time": "$(dashboard.params.time)",
            },
        })

        current_column += width
        current_row_height = max(current_row_height, height)
        if current_column >= DASHBOARD_GRID_COLUMNS:
            current_row += current_row_height
            current_column = 0
            current_row_height = 0

        # Build the embedded saved search definition
        tags = {}
        if query_info.get('tags'):
            tags["mitre_techniques"] = ",".join(query_info['tags'])
        if query_info.get('sigma_id'):
            tags["sigma_id"] = query_info['sigma_id']
        tags["platform"] = "soc-detection-rules"
        dashboard_meta = query_info.get("dashboard", {})
        if dashboard_meta.get("ask_ai_prompts"):
            tags["ask_ai_prompts"] = json.dumps(dashboard_meta["ask_ai_prompts"])
        if dashboard_meta.get("visualizationType"):
            tags["visualization_type"] = dashboard_meta["visualizationType"]

        ui_config = resolve_widget_ui_config(widget, query_info)

        saved_searches.append(build_saved_search_json(
            search_id=search_id,
            title=widget['title'],
            query=query_info['query'],
            description=query_info.get('description', ''),
            tags=tags,
            ui_config=ui_config,
        ))

    dashboard = {
        "dashboardId": dashboard_id,
        "providerId": "log-analytics",
        "providerName": "Log Analytics",
        "providerVersion": "3.0.0",
        "displayName": name,
        "description": description,
        "compartmentId": COMPARTMENT_ID,
        "isOobDashboard": False,
        "isShowInHome": True,
        "isShowDescription": True,
        "metadataVersion": "2.0",
        "type": "normal",
        "isFavorite": False,
        "nls": {},
        "uiConfig": {
            "isFilteringEnabled": True,
            "isRefreshEnabled": True,
        },
        "dataConfig": [],
        "screenImage": " ",
        "freeformTags": {"platform": "soc-detection-rules"},
        "parametersConfig": [
            {
                "paramName": "log-analytics-loggroup-filter",
                "displayName": "Log Group Compartment",
                "paramType": "LogAnalyticsLogGroupCompartment",
                "defaultValue": COMPARTMENT_ID,
                "isRequired": False,
            },
            {
                "paramName": "log-analytics-entity-filter",
                "displayName": "Entity",
                "paramType": "LogAnalyticsEntity",
                "defaultValue": "",
                "isRequired": False,
            },
            {
                "paramName": "time",
                "displayName": "Time Range",
                "paramType": "Time",
                "defaultValue": DEFAULT_DASHBOARD_TIME_PERIOD,
                "isRequired": False,
            },
        ],
        "tiles": tiles,
        "savedSearches": saved_searches,
    }

    return dashboard


def delete_existing_dashboard(md_client, display_name):
    """Delete any existing dashboard with the given name (dedup-safe).

    Uses OCID from list results for deletion (short dashboardId won't work
    for delete after OCI's soft-delete window).
    """
    try:
        dashboards = md_client.list_management_dashboards(
            compartment_id=COMPARTMENT_ID,
            display_name=display_name
        ).data.items
        for d in dashboards:
            try:
                md_client.delete_management_dashboard(d.dashboard_id)
                print(f"    - Deleted old dashboard: {display_name} ({d.dashboard_id})")
            except Exception as del_err:
                print(f"    - Could not delete dashboard {display_name}: {del_err}")
    except Exception as e:
        print(f"    - Could not list dashboards for '{display_name}': {e}")


def import_dashboard(md_client, dashboard_json, attempts=3):
    """Import a dashboard using the ManagementDashboardImportDetails API."""
    import_details = oci.management_dashboard.models.ManagementDashboardImportDetails(
        dashboards=[dashboard_json]
    )

    display_name = dashboard_json["displayName"]
    for attempt in range(1, attempts + 1):
        try:
            md_client.import_dashboard(import_details)
            print(f"  Imported dashboard: {display_name}")
            return True
        except oci.exceptions.ServiceError as exc:
            print(f"  Error importing '{display_name}': {exc.message[:200]}")
            return False
        except oci.exceptions.RequestException as exc:
            if attempt == attempts:
                print(f"  Error importing '{display_name}' after {attempts} attempts: {exc}")
                return False
            delay = attempt * 10
            print(
                f"  Retry {attempt}/{attempts - 1} importing '{display_name}' "
                f"after transient OCI request error: {exc}"
            )
            time.sleep(delay)


def cleanup_soc_content(md_client, dashboards=None):
    """Delete all SOC-related saved searches and dashboards."""
    dashboards = dashboards or DASHBOARDS
    print("\n  Cleaning up existing SOC content...")

    # Delete dashboards
    for dashboard_name in dashboards.keys():
        try:
            dashboard_items = md_client.list_management_dashboards(
                compartment_id=COMPARTMENT_ID,
                display_name=dashboard_name
            ).data.items
            for d in dashboard_items:
                try:
                    md_client.delete_management_dashboard(d.dashboard_id)
                    print(f"    - Deleted dashboard: {dashboard_name}")
                except Exception:
                    pass
        except Exception:
            pass

    # Delete saved searches
    all_widget_titles = set()
    for config in dashboards.values():
        for widget in config['widgets']:
            all_widget_titles.add(widget['title'])

    for title in all_widget_titles:
        try:
            searches = md_client.list_management_saved_searches(
                compartment_id=COMPARTMENT_ID,
                display_name=title
            ).data.items
            for s in searches:
                md_client.delete_management_saved_search(s.id)
                print(f"    - Deleted saved search: {title}")
        except Exception:
            pass

    print("  Cleanup complete.\n")


def validate_inventory_queries_in_oci(
    inventory,
    lookback=DEFAULT_QUERY_VALIDATION_LOOKBACK,
    query_timeout=60,
    progress=False,
    progress_interval=1,
    isolated=True,
):
    """Validate every unique inventory query in OCI before dashboard import."""
    namespace = resolve_validation_namespace(query_timeout)
    la_client = None if isolated else get_la_client(timeout=(10, query_timeout))

    query_files = sorted({widget["query_file"] for widget in iter_inventory_widgets(inventory)})
    seen = {}
    for index, query_file in enumerate(query_files, start=1):
        emit_progress = _should_emit_validation_progress(progress, progress_interval, index, len(query_files))
        if emit_progress:
            print(f"    [{index:03d}/{len(query_files):03d}] validating {query_file}", flush=True)
        query_info = load_query_info(query_file)
        if isolated:
            seen[query_file] = validate_query_in_oci_isolated(
                namespace=namespace,
                query_file=query_file,
                query_string=query_info["query"],
                lookback=lookback,
                query_timeout=query_timeout,
            )
        else:
            seen[query_file] = validate_query_in_oci(
                la_client=la_client,
                namespace=namespace,
                query_file=query_file,
                query_string=query_info["query"],
                lookback=lookback,
                timeout=query_timeout,
            )
        if emit_progress:
            print(_format_validation_progress(index, len(query_files), seen[query_file]), flush=True)

    return [seen[query_file] for query_file in query_files]


def deploy(
    cleanup=False,
    dry_run=False,
    live_validate=True,
    query_lookback=DEFAULT_QUERY_VALIDATION_LOOKBACK,
    query_timeout=60,
    validation_progress_interval=1,
    dashboard_names=None,
    allow_prod_write=False,
):
    print("=" * 60)
    print("OCI Log Analytics - SOC Dashboard Deployment")
    print("=" * 60)
    dlog = bind(
        log,
        compartment=COMPARTMENT_ID,
        cleanup=cleanup,
        dry_run=dry_run,
        live_validate=live_validate,
        targeted=bool(dashboard_names),
    )
    dlog.info("deploy.start")

    try:
        dashboards_to_deploy = select_dashboards(dashboard_names)
    except ValueError as exc:
        dlog.error("deploy.select_failed", extra={"error": str(exc)})
        print(f"\n  {exc}")
        raise SystemExit(1) from exc

    inventory = build_dashboard_inventory(dashboards=dashboards_to_deploy)
    inventory_errors = validate_dashboard_inventory(inventory)
    if inventory_errors:
        print("\n  Dashboard inventory validation failed:")
        for error in inventory_errors:
            print(f"    - {error}")
        raise SystemExit(1)

    if dry_run:
        print_dry_run_plan(inventory)
        return

    if live_validate:
        print(
            f"\n  Validating dashboard queries in OCI Log Analytics "
            f"(lookback={query_lookback}, timeout={query_timeout}s)..."
        )
        live_results = validate_inventory_queries_in_oci(
            inventory,
            lookback=query_lookback,
            query_timeout=query_timeout,
            progress=validation_progress_interval != 0,
            progress_interval=validation_progress_interval,
        )
        errors = [result for result in live_results if not result["ok"]]
        empty = [result for result in live_results if result["ok"] and result["empty"]]

        if errors:
            dlog.error(
                "deploy.live_validation_failed",
                extra={"failed": len(errors), "validated": len(live_results)},
            )
            print("  Query validation failed; no dashboards or saved searches will be imported.")
            for result in errors:
                print(f"    - {result['query_file']}: {result['error'][:180]}")
            raise SystemExit(1)

        print(f"  Validated {len(live_results)} unique query files in OCI Log Analytics.")
        if empty:
            print(f"  Note: {len(empty)} validated query files returned no rows in this window.")

    # Publish the dashboard-facing artifact only after local and optional live
    # validation pass. Dashboard import and saved-search mapping happen after this.
    if dashboard_names:
        print("\n  Targeted deployment: queries/dashboard_inventory.json was not rewritten.")
    else:
        write_dashboard_inventory(inventory=inventory)
        print(f"\n  Dashboard inventory: {DASHBOARD_INVENTORY_PATH}")

    # Tenancy safety: refuse mutating import/cleanup against emdemo (prod) outside
    # the LogAnalytics subtree unless the operator passed --i-understand-prod.
    try:
        assert_write_allowed(COMPARTMENT_ID, override=allow_prod_write)
    except ProdWriteGuardError as guard_err:
        dlog.error("deploy.prod_write_blocked", extra={"override": allow_prod_write})
        print(f"\n  {guard_err}")
        raise SystemExit(2) from guard_err

    md_client = get_dashboard_client()
    print(f"\n  Compartment: {COMPARTMENT_ID}")

    if cleanup:
        cleanup_soc_content(md_client, dashboards=dashboards_to_deploy)

    total_searches = 0
    total_dashboards = 0

    for dashboard_name, dashboard_config in dashboards_to_deploy.items():
        print(f"\n{'─' * 50}")
        print(f"  Dashboard: {dashboard_name}")
        print(f"  Widgets: {len(dashboard_config['widgets'])}")
        print(f"{'─' * 50}")

        # Load query data only after local and optional live validation pass.
        widget_queries = []
        for widget in dashboard_config['widgets']:
            rule_data = load_query_info(widget["query_file"])
            widget_queries.append(rule_data)
            print(f"    + Loaded: {widget['title']}")
            total_searches += 1

        # Build and import dashboard with embedded saved searches
        # Delete existing dashboard BEFORE generating new ID
        delete_existing_dashboard(md_client, dashboard_name)

        # Use timestamp suffix to avoid OCI soft-delete ID collisions
        ts = int(time.time())
        slug = dashboard_name.lower().replace(' ', '-').replace(':', '').replace('&', 'and')
        dashboard_id = f"soc-{slug}-{ts}"

        dashboard_json = build_dashboard_json(
            dashboard_id=dashboard_id,
            name=dashboard_name,
            description=dashboard_config['description'],
            widgets=dashboard_config['widgets'],
            widget_queries=widget_queries,
        )

        if import_dashboard(md_client, dashboard_json):
            total_dashboards += 1

    # Summary
    print_deployment_summary(total_searches, total_dashboards)
    dlog.info(
        "deploy.done",
        extra={"dashboards_imported": total_dashboards, "saved_searches": total_searches},
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy SOC dashboards to OCI Log Analytics")
    parser.add_argument('--cleanup', action='store_true',
                        help='Delete existing SOC saved searches and dashboards before deploying')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print deployment plan and validate query files without executing')
    parser.add_argument('--validate', action='store_true',
                        help='Run pre-flight validation checks')
    parser.add_argument('--export-inventory', action='store_true',
                        help='Generate queries/dashboard_inventory.json and exit')
    parser.add_argument('--inventory-path', default=DASHBOARD_INVENTORY_PATH,
                        help='Output path for --export-inventory')
    parser.add_argument('--skip-live-validation', action='store_true',
                        help='Skip live OCI query validation before dashboard import')
    parser.add_argument('--query-lookback', default=DEFAULT_QUERY_VALIDATION_LOOKBACK,
                        help='Lookback window for live OCI query validation')
    parser.add_argument('--query-timeout', type=int, default=60,
                        help='Per-query timeout in seconds for live OCI query validation')
    parser.add_argument('--validation-progress-interval', type=int, default=1,
                        help='Print live query validation progress every N queries; 0 disables progress')
    parser.add_argument('--dashboard-name', action='append', dest='dashboard_names',
                        help='Deploy only the named dashboard. Can be supplied multiple times.')
    parser.add_argument('--i-understand-prod', action='store_true', dest='i_understand_prod',
                        help='Acknowledge a deliberate write against the emdemo PRODUCTION '
                             'tenancy outside the LogAnalytics subtree (or set OCI_ALLOW_PROD_WRITE=1).')
    args = parser.parse_args()

    if args.validate:
        ok = validate_oci_setup(['ocid', 'cli', 'namespace', 'compartment', 'query_files'])
        inventory = build_dashboard_inventory()
        inventory_errors = validate_dashboard_inventory(inventory)
        for error in inventory_errors:
            print(f"  [ERR ] Dashboard inventory: {error}")
        ok = ok and not inventory_errors
        sys.exit(0 if ok else 1)

    if args.export_inventory:
        path = write_dashboard_inventory(path=args.inventory_path)
        print(f"Dashboard inventory written to: {path}")
        sys.exit(0)

    deploy(
        cleanup=args.cleanup,
        dry_run=args.dry_run,
        live_validate=not args.skip_live_validation,
        query_lookback=args.query_lookback,
        query_timeout=args.query_timeout,
        validation_progress_interval=args.validation_progress_interval,
        dashboard_names=args.dashboard_names,
        allow_prod_write=args.i_understand_prod,
    )
