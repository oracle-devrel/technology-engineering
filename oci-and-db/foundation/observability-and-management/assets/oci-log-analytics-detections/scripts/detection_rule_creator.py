#!/usr/bin/env python3
"""Build scheduled-search detection rule specs from query JSON artifacts.

This utility does not call OCI directly. It classifies which saved-search
queries are compatible with scheduled-search detection rules and emits a
portable JSON spec that can be turned into OCI Monitoring-backed rules.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from oci_config import APPS_DIR, HUNTING_DIR, PROJECT_DIR, QUERIES_DIR
from query_artifacts import is_saved_search_query_file

UNSUPPORTED_SCHEDULED_COMMANDS = {
    "cluster",
    "clustercompare",
    "clusterdetails",
    "clustersplit",
    "compare",
    "createview",
    "delta",
    "fieldsummary",
    "geostats",
    "highlightgroups",
    "linkdetails",
    "map",
    "nlp",
    "timecompare",
}

DASHBOARD_ONLY_VISUALIZATIONS = {"cluster", "issues", "link", "map"}
AGGREGATE_RE = re.compile(
    r"\b(?:count|sum|max|min|avg|average|distinctcount|unique)\s+as\s+([A-Za-z_][A-Za-z0-9_]*)",
    re.IGNORECASE,
)
BY_RE = re.compile(r"\b(?:stats|timestats)\b.*?\bby\b(?P<fields>.+?)(?:\||$)", re.IGNORECASE)
UNSUPPORTED_QUERY_PATTERNS = [
    (re.compile(r"\bregexextract\s*\(", re.IGNORECASE), "unsupported scheduled-search function: regexextract"),
    (re.compile(r"\bcountif\s*\(", re.IGNORECASE), "unsupported scheduled-search aggregate: countif"),
    (re.compile(r"\|\s*timecluster\b", re.IGNORECASE), "unsupported scheduled-search command: timecluster"),
    (re.compile(r"\beval\b[^|]*\bcase\s*\(", re.IGNORECASE), "unsupported scheduled-search eval: case"),
    (re.compile(r"'New Process Name'", re.IGNORECASE), "field not mapped in demo sources: New Process Name"),
    (re.compile(r"\bProperties\b", re.IGNORECASE), "field not mapped in demo sources: Properties"),
    (re.compile(r"Fusion Apps:", re.IGNORECASE), "query depends on unavailable Fusion Apps demo sources"),
]
OUTPUT_JSON = Path(QUERIES_DIR) / "detection_rule_specs.json"


def load_query_payloads() -> list[tuple[str, dict]]:
    """Load all query JSON artifacts across supported surfaces."""
    roots = [
        Path(QUERIES_DIR),
        Path(APPS_DIR),
        Path(HUNTING_DIR),
    ]
    seen: set[Path] = set()
    payloads: list[tuple[str, dict]] = []

    for root in roots:
        for path in sorted(root.glob("*.json")):
            if path in seen:
                continue
            if not is_saved_search_query_file(path):
                continue
            seen.add(path)
            with path.open() as f:
                payload = json.load(f)
            if "query" not in payload or "title" not in payload:
                continue
            payloads.append((str(path.relative_to(PROJECT_DIR)), payload))

    return payloads


def _extract_dimensions(query: str) -> list[str]:
    match = BY_RE.search(query)
    if not match:
        return []

    fields_clause = re.sub(r"\bspan\s*=\s*[^|,]+", "", match.group("fields"), flags=re.IGNORECASE).strip()
    fields = []
    for raw_field in fields_clause.split(","):
        field = raw_field.strip().strip("'").strip('"')
        if field:
            fields.append(field)
    return fields


def classify_query(query: str, visualization_type: str | None = None) -> dict:
    """Determine whether a query is suitable for a scheduled-search rule."""
    reasons: list[str] = []
    lowered = query.lower()

    for command in sorted(UNSUPPORTED_SCHEDULED_COMMANDS):
        if re.search(rf"\|\s*{re.escape(command)}\b", lowered):
            reasons.append(f"unsupported scheduled-search command: {command}")

    for pattern, reason in UNSUPPORTED_QUERY_PATTERNS:
        if pattern.search(query):
            reasons.append(reason)

    if visualization_type in DASHBOARD_ONLY_VISUALIZATIONS:
        reasons.append(f"dashboard-only visualization type: {visualization_type}")

    metric_aliases = AGGREGATE_RE.findall(query)
    metric_name = metric_aliases[0] if metric_aliases else None
    if not metric_name:
        reasons.append("query does not expose an explicit aggregate metric alias")

    dimensions = _extract_dimensions(query)
    if len(dimensions) > 3:
        reasons.append("scheduled-search rules support at most 3 dimensions")

    return {
        "eligible": not reasons,
        "metric_name": metric_name,
        "dimensions": dimensions[:3],
        "reasons": reasons,
    }


def build_detection_rule_spec(query_path: str, payload: dict) -> dict:
    """Build a portable scheduled-search detection rule spec."""
    dashboard_meta = payload.get("dashboard", {})
    classification = classify_query(
        payload["query"],
        visualization_type=dashboard_meta.get("visualizationType"),
    )

    title = payload["title"]
    metric_name = classification["metric_name"] or re.sub(r"[^A-Za-z0-9]+", "_", title).strip("_")
    scheduled_rule_eligibility = "deployable" if classification["eligible"] else "not_deployable"
    dashboard_readiness = "dashboard_ready" if dashboard_meta else "not_dashboard_annotated"
    source_confidence = payload.get("source_confidence") or ("high" if payload.get("sigma_id") else "medium")
    test_data_coverage = payload.get("test_data_coverage") or (
        "covered" if payload.get("atomic_red_team", {}).get("has_tests") else "not_evaluated"
    )

    return {
        "query_file": query_path,
        "title": title,
        "severity": payload.get("level", "medium"),
        "eligible": classification["eligible"],
        "metric_name": metric_name,
        "dimensions": classification["dimensions"],
        "schedule": payload.get("detection_rule", {}).get("schedule", "5m"),
        "lookback": payload.get("detection_rule", {}).get("lookback", "15m"),
        "query": payload["query"],
        "reasons": classification["reasons"],
        "detection_maturity": payload.get("detection_maturity", "validated_locally" if payload.get("query") else "draft"),
        "source_confidence": source_confidence,
        "field_coverage": payload.get("field_coverage", "not_evaluated"),
        "test_data_coverage": test_data_coverage,
        "live_validation_status": payload.get("live_validation_status", "not_run"),
        "dashboard_readiness": dashboard_readiness,
        "scheduled_rule_eligibility": scheduled_rule_eligibility,
        "alarm_template": {
            "enabled": classification["eligible"],
            "namespace": "oci_log_analytics_detections",
            "metric_name": metric_name,
            "dimensions": classification["dimensions"],
            "severity": payload.get("level", "medium"),
            "create_alarm_by_default": False,
        },
    }


def build_catalog(payloads: list[tuple[str, dict]] | None = None) -> dict:
    """Build detection-rule specs for all query artifacts."""
    payloads = payloads if payloads is not None else load_query_payloads()
    specs = [build_detection_rule_spec(path, payload) for path, payload in payloads]
    eligible = [spec for spec in specs if spec["eligible"]]
    ineligible = [spec for spec in specs if not spec["eligible"]]

    return {
        "total_queries": len(specs),
        "eligible_queries": len(eligible),
        "ineligible_queries": len(ineligible),
        "specs": specs,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build scheduled-search detection rule specs")
    parser.add_argument("--out", help=f"Optional JSON output path (for example {OUTPUT_JSON})")
    parser.add_argument("--write-default", action="store_true", help=f"Write {OUTPUT_JSON}")
    parser.add_argument("--eligible-only", action="store_true", help="Only print eligible rule specs")
    args = parser.parse_args()

    catalog = build_catalog()
    specs = catalog["specs"]
    if args.eligible_only:
        specs = [spec for spec in specs if spec["eligible"]]

    output_path = args.out or (str(OUTPUT_JSON) if args.write_default else "")
    if output_path:
        out_path = Path(output_path)
        out_path.write_text(json.dumps({**catalog, "specs": specs}, indent=2))
        print(f"Wrote detection rule specs to {out_path}")
        return

    print("=" * 60)
    print("Scheduled-Search Detection Rule Creator")
    print("=" * 60)
    print(f"Total queries:    {catalog['total_queries']}")
    print(f"Eligible:         {catalog['eligible_queries']}")
    print(f"Ineligible:       {catalog['ineligible_queries']}")

    for spec in specs:
        status = "ELIGIBLE" if spec["eligible"] else "SKIP"
        print(f"\n[{status}] {spec['query_file']}")
        print(f"  title:      {spec['title']}")
        print(f"  metric:     {spec['metric_name']}")
        print(f"  dimensions: {', '.join(spec['dimensions']) or '-'}")
        if spec["reasons"]:
            print(f"  reasons:    {'; '.join(spec['reasons'])}")


if __name__ == "__main__":
    main()
