#!/usr/bin/env python3
"""Build and generate the scoped Octo APM workshop deployment surface.

The bundle intentionally contains only variable-safe metadata: query text,
field names/raw paths, widget metadata, and detection-rule specs. It excludes
live OCIDs, hostnames, IPs, field example values, and health evidence.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from deploy_dashboard import DASHBOARDS
from detection_rule_creator import build_detection_rule_spec
from generate_test_logs import (
    OUTPUT_DIR,
    expand_events_over_days,
    generate_application_events,
    write_jsonl,
)
from oci_config import PROJECT_DIR, QUERIES_DIR
from query_artifacts import is_saved_search_query_file
from test_data_manifest import rebuild_manifest


DASHBOARD_NAME = "OCI-DEMO: Octo APM Demo Dashboard"
OCTO_WORKSHOP_DATA_FILE = "octo_apm_workshop_application_logs.jsonl"
DEFAULT_BUNDLE_PATH = Path(QUERIES_DIR) / "octo_apm_workshop_bundle.json"
OCTO_LOG_SOURCE = "SOC Application Logs"

DETECTION_RULE_QUERY_FILES = [
    "apps/apm_octo_rule_api_gateway_threat_count.json",
    "apps/apm_octo_rule_compromised_vm_count.json",
    "apps/apm_octo_rule_java_payment_error_count.json",
    "apps/apm_octo_rule_payment_interception_count.json",
    "apps/apm_octo_rule_payment_redirect_count.json",
]

REQUIRED_FIELD_NAMES = {
    "APM Domain",
    "API Gateway Action",
    "API Gateway Policy Decision",
    "API Gateway Request ID",
    "API Gateway Route",
    "API Gateway Threat Signal",
    "Attack ID",
    "Attack Stage",
    "Compromised VM",
    "DB Connection Name",
    "DB Elapsed ms",
    "DB Statement",
    "DB Target",
    "Destination IP",
    "Destination Port",
    "Error Type",
    "Host Name",
    "Host Role",
    "HTTP Redirect Location",
    "Instance OCID",
    "Java APM Error Type",
    "Java APM Latency ms",
    "Java APM Path",
    "Metric Name",
    "Metric Unit",
    "Metric Value",
    "MITRE Tactic",
    "MITRE Technique ID",
    "OSQuery Finding",
    "OSQuery Query",
    "OSQuery SQL",
    "Parent Span ID",
    "Payment Interception",
    "Payment Provider",
    "Payment Redirect",
    "Payment Redirect URL",
    "Payment Risk Score",
    "Process Command Line",
    "Request ID",
    "Response Code",
    "Run ID",
    "Security Severity",
    "Service Name",
    "Service Namespace",
    "Span Attributes",
    "Span ID",
    "Span Kind",
    "Span Name",
    "Trace ID",
    "Workflow ID",
    "Workflow Step",
}

SENSITIVE_BUNDLE_PATTERNS = (
    re.compile(r"\bocid1\.", re.IGNORECASE),
    re.compile(r"\bopc-request-id\b", re.IGNORECASE),
    re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    re.compile(r"\boctodemo\.cloud\b", re.IGNORECASE),
)


def query_files_for_dashboard(dashboard_name: str = DASHBOARD_NAME) -> list[str]:
    """Return dashboard query files for the requested dashboard."""
    if dashboard_name not in DASHBOARDS:
        raise ValueError(f"Unknown dashboard: {dashboard_name}")
    return [widget["query_file"] for widget in DASHBOARDS[dashboard_name]["widgets"]]


def _load_json(relative_query_path: str) -> dict:
    path = Path(QUERIES_DIR) / relative_query_path
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _safe_query_asset(query_file: str) -> dict:
    payload = _load_json(query_file)
    dashboard_meta = payload.get("dashboard", {})
    return {
        "query_file": query_file,
        "title": payload["title"],
        "description": payload.get("description", ""),
        "level": payload.get("level", "informational"),
        "query": payload["query"],
        "logsource": payload.get("logsource", {}),
        "tags": payload.get("tags", []),
        "visualization_type": dashboard_meta.get("visualizationType"),
        "visualization_options": dashboard_meta.get("options", {}),
    }


def _source_names(field: dict) -> set[str]:
    return {
        source.get("source_display", "")
        for source in field.get("sources", [])
        if source.get("source_display")
    }


def _load_scoped_fields(query_files: Iterable[str]) -> list[dict]:
    dictionary_path = Path(QUERIES_DIR) / "log_source_field_dictionary.json"
    with dictionary_path.open(encoding="utf-8") as f:
        dictionary = json.load(f)

    query_file_set = set(query_files)
    scoped_fields = []
    for field in dictionary.get("fields", []):
        display_name = field.get("display_name", "")
        used_by = sorted(set(field.get("queries_using_it", [])) & query_file_set)
        source_ok = (
            OCTO_LOG_SOURCE in _source_names(field)
            or "application_logs" in field.get("source_candidate_groups", [])
        )
        required = display_name in REQUIRED_FIELD_NAMES
        if not source_ok or (not required and not used_by):
            continue
        scoped_fields.append({
            "display_name": display_name,
            "kind": field.get("kind", ""),
            "type": field.get("type", ""),
            "raw_json_paths": field.get("raw_json_paths", []),
            "source_candidate_groups": field.get("source_candidate_groups", []),
            "queries_using_it": used_by,
        })

    return sorted(scoped_fields, key=lambda item: item["display_name"])


def _build_detection_rule_specs() -> list[dict]:
    specs = []
    for query_file in DETECTION_RULE_QUERY_FILES:
        payload = _load_json(query_file)
        specs.append(build_detection_rule_spec(f"queries/{query_file}", payload))
    return specs


def build_bundle(generated_at: str | None = None) -> dict:
    """Build the scoped Octo APM workshop bundle."""
    generated_at = generated_at or datetime.now(timezone.utc).isoformat()
    dashboard_query_files = query_files_for_dashboard(DASHBOARD_NAME)
    all_query_files = dashboard_query_files + DETECTION_RULE_QUERY_FILES
    widgets = [
        {
            "title": widget["title"],
            "query_file": widget["query_file"],
            "time_selection": widget.get("time_selection", {}),
        }
        for widget in DASHBOARDS[DASHBOARD_NAME]["widgets"]
    ]
    detection_specs = _build_detection_rule_specs()
    deployable_specs = [spec for spec in detection_specs if spec["eligible"]]

    return {
        "version": 1,
        "generated_at": generated_at,
        "scope": "octo-apm-demo-workshop",
        "log_source": OCTO_LOG_SOURCE,
        "dashboard": {
            "name": DASHBOARD_NAME,
            "description": DASHBOARDS[DASHBOARD_NAME]["description"],
            "widget_count": len(widgets),
            "widgets": widgets,
        },
        "queries": [_safe_query_asset(query_file) for query_file in all_query_files],
        "fields": _load_scoped_fields(all_query_files),
        "detection_rules": {
            "spec_count": len(detection_specs),
            "deployable_count": len(deployable_specs),
            "metadata_only": True,
            "specs": detection_specs,
        },
        "synthetic_data": {
            "filename": OCTO_WORKSHOP_DATA_FILE,
            "source": OCTO_LOG_SOURCE,
            "generator": "scripts/octo_apm_workshop.py --generate-data",
        },
        "deployment": {
            "environment_variables": [
                "OCI_PROFILE",
                "OCI_COMPARTMENT_ID",
                "OCI_TENANCY_ID",
                "LA_NAMESPACE",
                "LOG_ANALYTICS_LOG_GROUP_ID",
                "DETECTIONS_REPO",
            ],
            "commands": [
                "python3 scripts/setup_log_sources.py --octo-apm-only",
                "python3 scripts/octo_apm_workshop.py --generate-data --days ${OCTO_WORKSHOP_DAYS}",
                f"python3 scripts/ingest_test_data.py --mode direct --file {OCTO_WORKSHOP_DATA_FILE}",
                "python3 scripts/detection_rule_creator.py --write-default",
                f"python3 scripts/deploy_dashboard.py --dashboard-name \"{DASHBOARD_NAME}\" --query-lookback ${{OCTO_WORKSHOP_LOOKBACK}} --query-timeout ${{OCTO_WORKSHOP_QUERY_TIMEOUT}}",
                f"python3 scripts/verify_deployed_dashboards.py --dashboard-name \"{DASHBOARD_NAME}\" --lookback ${{OCTO_WORKSHOP_LOOKBACK}} --query-timeout ${{OCTO_WORKSHOP_QUERY_TIMEOUT}}",
            ],
        },
    }


def _query_reference_errors(query_file: str, label: str) -> list[str]:
    errors = []
    if not query_file:
        return [f"{label}: missing query_file"]
    if not is_saved_search_query_file(query_file):
        errors.append(f"{label}: {query_file} is not a saved-search query file")
    query_path = Path(QUERIES_DIR) / query_file
    if not query_path.exists():
        errors.append(f"{label}: missing query file {query_file}")
    return errors


def validate_bundle(bundle: dict) -> list[str]:
    """Validate the scoped Octo APM workshop bundle contract."""
    errors: list[str] = []
    if not isinstance(bundle, dict):
        return ["bundle: expected object"]

    if bundle.get("scope") != "octo-apm-demo-workshop":
        errors.append("scope: expected octo-apm-demo-workshop")
    if bundle.get("log_source") != OCTO_LOG_SOURCE:
        errors.append(f"log_source: expected {OCTO_LOG_SOURCE}")

    dashboard = bundle.get("dashboard", {})
    if dashboard.get("name") != DASHBOARD_NAME:
        errors.append(f"dashboard.name: expected {DASHBOARD_NAME}")
    widgets = dashboard.get("widgets", [])
    if dashboard.get("widget_count") != len(widgets):
        errors.append("dashboard.widget_count mismatch")
    for index, widget in enumerate(widgets, start=1):
        query_file = widget.get("query_file", "")
        errors.extend(_query_reference_errors(query_file, f"dashboard.widgets[{index}]"))
        if query_file and not query_file.startswith("apps/apm_octo_"):
            errors.append(f"dashboard.widgets[{index}]: {query_file} is outside apps/apm_octo_* scope")

    for index, query in enumerate(bundle.get("queries", []), start=1):
        errors.extend(_query_reference_errors(query.get("query_file", ""), f"queries[{index}]"))
        if not query.get("query"):
            errors.append(f"queries[{index}]: missing query text")

    field_names = {field.get("display_name", "") for field in bundle.get("fields", [])}
    missing_fields = sorted(REQUIRED_FIELD_NAMES - field_names)
    if missing_fields:
        errors.append(f"fields: missing required field(s): {missing_fields}")

    detection_rules = bundle.get("detection_rules", {})
    specs = detection_rules.get("specs", [])
    if detection_rules.get("spec_count") != len(specs):
        errors.append("detection_rules.spec_count mismatch")
    deployable_count = sum(1 for spec in specs if spec.get("eligible"))
    if detection_rules.get("deployable_count") != deployable_count:
        errors.append("detection_rules.deployable_count mismatch")

    synthetic_data = bundle.get("synthetic_data", {})
    if synthetic_data.get("filename") != OCTO_WORKSHOP_DATA_FILE:
        errors.append(f"synthetic_data.filename: expected {OCTO_WORKSHOP_DATA_FILE}")
    if synthetic_data.get("source") != OCTO_LOG_SOURCE:
        errors.append(f"synthetic_data.source: expected {OCTO_LOG_SOURCE}")

    deployment = bundle.get("deployment", {})
    env_vars = set(deployment.get("environment_variables", []))
    required_env = {
        "OCI_PROFILE",
        "OCI_COMPARTMENT_ID",
        "OCI_TENANCY_ID",
        "LA_NAMESPACE",
        "LOG_ANALYTICS_LOG_GROUP_ID",
        "DETECTIONS_REPO",
    }
    missing_env = sorted(required_env - env_vars)
    if missing_env:
        errors.append(f"deployment.environment_variables: missing {missing_env}")
    if not deployment.get("commands"):
        errors.append("deployment.commands: missing commands")

    serialized = json.dumps(bundle, sort_keys=True)
    for pattern in SENSITIVE_BUNDLE_PATTERNS:
        if pattern.search(serialized):
            errors.append(f"bundle: sensitive live value matched {pattern.pattern!r}")
            break

    return errors


def filter_octo_events(events: Iterable[dict]) -> list[dict]:
    """Return only Octo namespace application events, preserving input objects."""
    return [
        {**event}
        for event in events
        if event.get("service.namespace") == "octo"
    ]


def generate_octo_workshop_data(days: int, output_dir: Path = OUTPUT_DIR) -> dict:
    """Write the Octo-only application log dataset and refresh the manifest."""
    output_dir.mkdir(parents=True, exist_ok=True)
    events = filter_octo_events(generate_application_events())
    expanded_events = expand_events_over_days(events, days)
    count = write_jsonl(output_dir / OCTO_WORKSHOP_DATA_FILE, expanded_events)
    manifest = rebuild_manifest(output_dir)
    return {
        "filename": OCTO_WORKSHOP_DATA_FILE,
        "event_count": count,
        "days": days,
        "manifest_total_events": manifest["total_events"],
    }


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be greater than 0")
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the scoped Octo APM workshop assets")
    parser.add_argument("--export-bundle", action="store_true", help=f"Write {DEFAULT_BUNDLE_PATH}")
    parser.add_argument("--out", default=str(DEFAULT_BUNDLE_PATH), help="Bundle output path")
    parser.add_argument("--validate-bundle", action="store_true", help="Validate the generated or existing bundle")
    parser.add_argument("--generate-data", action="store_true", help=f"Write test_data/{OCTO_WORKSHOP_DATA_FILE}")
    parser.add_argument("--days", type=positive_int, default=21, help="Synthetic data day count")
    parser.add_argument("--summary", action="store_true", help="Print the scoped asset summary")
    args = parser.parse_args()

    if args.export_bundle:
        bundle = build_bundle()
        output_path = Path(args.out)
        output_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
        print(f"Wrote Octo APM workshop bundle to {output_path.relative_to(Path(PROJECT_DIR)) if output_path.is_relative_to(Path(PROJECT_DIR)) else output_path}")

    if args.validate_bundle:
        bundle_path = Path(args.out)
        if bundle_path.exists():
            bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        else:
            bundle = build_bundle()
        errors = validate_bundle(bundle)
        if errors:
            print("Octo APM workshop bundle validation failed:")
            for error in errors:
                print(f"  - {error}")
            return 1
        print("Octo APM workshop bundle validation passed")

    if args.generate_data:
        result = generate_octo_workshop_data(args.days)
        print(
            f"Wrote {result['event_count']} Octo APM workshop events "
            f"for {result['days']} day(s) to test_data/{result['filename']}"
        )

    if args.summary or (not args.export_bundle and not args.generate_data and not args.validate_bundle):
        bundle = build_bundle()
        print("Octo APM Workshop Scope")
        print(f"  dashboard:       {bundle['dashboard']['name']}")
        print(f"  widgets:         {bundle['dashboard']['widget_count']}")
        print(f"  queries:         {len(bundle['queries'])}")
        print(f"  fields:          {len(bundle['fields'])}")
        print(f"  detection rules: {bundle['detection_rules']['deployable_count']} deployable specs")
        print(f"  data file:       {bundle['synthetic_data']['filename']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
