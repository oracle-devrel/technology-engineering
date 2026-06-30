#!/usr/bin/env python3
"""Build SIEM migration discovery inventories and OCI readiness reports."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from scripts.convert_sentinel_kql import (  # noqa: E402
    DEFAULT_CANDIDATES_FILE,
    extract_source_tables,
    load_mapping_config,
)
from scripts.sentinel_conversion_workflow import classify_next_query_candidate  # noqa: E402
from scripts.sync_sentinel_kql import (  # noqa: E402
    build_candidate_export,
    load_sentinel_candidates,
    resolve_sentinel_commit,
)

DEFAULT_INVENTORY_PATH = PROJECT_DIR / "queries" / "siem_discovery_inventory.json"
DEFAULT_REPORT_DIR = PROJECT_DIR / "docs" / "health"
DEFAULT_FIELD_DICTIONARY = PROJECT_DIR / "queries" / "log_source_field_dictionary.json"
DEFAULT_MIGRATION_PLAN = PROJECT_DIR / "queries" / "migration_plan_sentinel.json"
SCHEMA_DIR = PROJECT_DIR / "schemas" / "migration"
DISCOVERY_SCHEMA = SCHEMA_DIR / "discovery_inventory.schema.json"
MIGRATION_REPORT_SCHEMA = SCHEMA_DIR / "migration_report.schema.json"
MIGRATION_PLAN_SCHEMA = SCHEMA_DIR / "migration_plan.schema.json"
BLOCKER_TYPES = {
    "field_mapping",
    "table_mapping",
    "local_validation",
    "live_validation",
    "live_environment",
    "kql_support",
    "unsupported",
    "parser_readiness",
}
IDENTIFIER_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\b")
REDACTIONS = (
    (re.compile(r"\bocid1\.[A-Za-z0-9_.-]+\b"), "<redacted:ocid>"),
    (re.compile(r"\b(?:25[0-5]|2[0-4]\d|1?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}\b"), "<redacted:ip>"),
    (re.compile(r"\bopc[-_]request[-_]id\s*[:=]\s*[A-Za-z0-9_.:-]+", re.I), "opc-request-id=<redacted>"),
    (re.compile(r"\bhttps://login\.microsoftonline\.com/[A-Za-z0-9-]+", re.I), "https://login.microsoftonline.com/<redacted:tenant>"),
)
KQL_KEYWORDS = {
    "ago",
    "and",
    "asc",
    "by",
    "contains",
    "count",
    "countif",
    "datetime",
    "desc",
    "distinct",
    "extend",
    "false",
    "in",
    "join",
    "let",
    "make_set",
    "not",
    "or",
    "project",
    "sort",
    "summarize",
    "table",
    "take",
    "true",
    "union",
    "where",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def validate_payload_against_schema(payload: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    """Validate the JSON Schema subset used by migration artifact contracts."""
    errors: list[str] = []
    expected_type = schema.get("type")
    if expected_type:
        validators = {
            "object": lambda value: isinstance(value, dict),
            "array": lambda value: isinstance(value, list),
            "string": lambda value: isinstance(value, str),
            "integer": lambda value: isinstance(value, int) and not isinstance(value, bool),
            "boolean": lambda value: isinstance(value, bool),
        }
        validator = validators.get(expected_type)
        if validator and not validator(payload):
            errors.append(f"{path}: expected {expected_type}")
            return errors

    if "enum" in schema and payload not in schema["enum"]:
        errors.append(f"{path}: expected one of {schema['enum']}")

    if expected_type == "integer" and "minimum" in schema and payload < schema["minimum"]:
        errors.append(f"{path}: expected >= {schema['minimum']}")

    if expected_type == "object":
        for field in schema.get("required", []):
            if field not in payload:
                errors.append(f"{path}: missing required field {field}")
        for field, child_schema in schema.get("properties", {}).items():
            if field in payload:
                errors.extend(validate_payload_against_schema(payload[field], child_schema, f"{path}.{field}"))

    if expected_type == "array" and "items" in schema:
        child_schema = schema["items"]
        for index, item in enumerate(payload):
            errors.extend(validate_payload_against_schema(item, child_schema, f"{path}[{index}]"))
    return errors


def validate_artifact_schema(payload: dict[str, Any], schema_path: Path) -> None:
    schema = _read_json(schema_path)
    errors = validate_payload_against_schema(payload, schema)
    if errors:
        preview = "\n".join(f"  - {error}" for error in errors[:20])
        raise ValueError(f"{schema_path.name} validation failed:\n{preview}")


def redact_sensitive_values(value: Any) -> Any:
    if isinstance(value, str):
        redacted = value
        for pattern, replacement in REDACTIONS:
            redacted = pattern.sub(replacement, redacted)
        return redacted
    if isinstance(value, list):
        return [redact_sensitive_values(item) for item in value]
    if isinstance(value, dict):
        return {key: redact_sensitive_values(nested) for key, nested in value.items()}
    return value


def _load_field_names(path: Path = DEFAULT_FIELD_DICTIONARY) -> set[str]:
    if not path.exists():
        return set()
    payload = _read_json(path)
    names = {field.get("display_name", "") for field in payload.get("fields", [])}
    names |= set(payload.get("approved_builtins", []))
    return {name for name in names if name}


def _field_usage(query: str, known_fields: set[str], mapped_fields: set[str]) -> list[str]:
    candidates = set()
    for match in IDENTIFIER_RE.finditer(query or ""):
        token = match.group(1)
        if token.lower() in KQL_KEYWORDS:
            continue
        if token in mapped_fields or token in known_fields:
            candidates.add(token)
    return sorted(candidates)


def _parse_externaldata_columns(schema: str) -> list[dict[str, str]]:
    columns = []
    for raw_column in [part.strip() for part in schema.split(",") if part.strip()]:
        if ":" in raw_column:
            name, data_type = raw_column.split(":", 1)
        else:
            name, data_type = raw_column, "string"
        column = {"name": name.strip().strip("`'\" "), "type": data_type.strip().strip("`'\" ")}
        if column["name"]:
            columns.append(column)
    return columns


def _parse_externaldata_options(options: str) -> dict[str, str]:
    parsed = {}
    for raw_option in [part.strip() for part in options.split(",") if part.strip()]:
        if "=" not in raw_option:
            continue
        key, value = raw_option.split("=", 1)
        parsed[key.strip()] = value.strip().strip("'\"")
    return parsed


def _externaldata_binding_name(query: str, start: int, fallback_index: int) -> str:
    prefix = query[max(0, start - 160):start]
    match = re.search(
        r"let\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*\(*\s*(?:materialize\s*\(\s*)?$",
        prefix,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if match:
        return match.group("name")
    return f"externaldata_{fallback_index}"


def extract_externaldata_dependencies(query: str) -> list[dict[str, Any]]:
    """Return remote feed dependencies used by Sentinel ``externaldata`` calls."""

    dependencies = []
    pattern = re.compile(
        r"externaldata\s*\((?P<schema>.*?)\)\s*"
        r"\[\s*(?:[A-Za-z]@|@)?(?P<quote>['\"])(?P<url>.*?)(?P=quote)\s*\]\s*"
        r"(?:with\s*\((?P<options>.*?)\))?",
        flags=re.IGNORECASE | re.DOTALL,
    )
    for index, match in enumerate(pattern.finditer(query or ""), start=1):
        options = _parse_externaldata_options(match.group("options") or "")
        dependencies.append({
            "kind": "externaldata",
            "name": _externaldata_binding_name(query or "", match.start(), index),
            "url": match.group("url"),
            "format": options.get("format", "csv"),
            "columns": _parse_externaldata_columns(match.group("schema") or ""),
            "options": options,
            "staging": {
                "target": "oci_lookup_or_custom_log",
                "source_candidates": ["Azure Log Analytics Custom Logs", "SOC Application Logs"],
            },
        })
    return dependencies


def _source_info(tables: list[str], mapping: dict[str, Any]) -> tuple[list[str], list[str]]:
    mapped: list[str] = []
    missing: list[str] = []
    for table in tables:
        spec = mapping.get("tables", {}).get(table)
        if not spec:
            missing.append(table)
            continue
        for source in spec.get("sources", []):
            if source not in mapped:
                mapped.append(source)
    return mapped, missing


def _missing_fields(fields: list[str], mapping: dict[str, Any], known_fields: set[str]) -> list[str]:
    mapped_fields = set(mapping.get("fields", {}))
    return sorted(field for field in fields if field not in mapped_fields and field not in known_fields)


def _blockers(missing_tables: list[str], missing_fields: list[str]) -> list[dict[str, str]]:
    blockers = []
    for table in missing_tables:
        blockers.append({"type": "table_mapping", "detail": table})
    for field in missing_fields:
        blockers.append({"type": "field_mapping", "detail": field})
    return blockers


def _status_for(blockers: list[dict[str, str]]) -> str:
    return "blocked" if blockers else "ready_for_local_validation"


def sentinel_inventory(candidates: list[dict[str, Any]], source: dict[str, Any]) -> dict[str, Any]:
    mapping = load_mapping_config()
    known_fields = _load_field_names()
    mapped_fields = set(mapping.get("fields", {}))
    items = []
    table_counts: Counter[str] = Counter()
    blocker_counts: Counter[str] = Counter()

    for candidate in candidates:
        tables = [
            table for table in extract_source_tables(candidate.get("query", ""))
            if table.lower() not in KQL_KEYWORDS
        ]
        fields = _field_usage(candidate.get("query", ""), known_fields, mapped_fields)
        mapped_sources, missing_tables = _source_info(tables, mapping)
        missing_fields = _missing_fields(fields, mapping, known_fields)
        feed_dependencies = extract_externaldata_dependencies(candidate.get("query", ""))
        blockers = _blockers(missing_tables, missing_fields)
        table_counts.update(tables)
        blocker_counts.update(blocker["type"] for blocker in blockers)
        items.append({
            "content_id": candidate.get("sentinel_id") or candidate.get("source_path", ""),
            "title": candidate.get("title", ""),
            "kind": candidate.get("kind", "analytics_rule"),
            "source_path": candidate.get("source_path", ""),
            "source_url": candidate.get("source_url", ""),
            "enabled": bool(candidate.get("enabled", True)),
            "severity": candidate.get("severity", "medium"),
            "schedule": {
                "frequency": candidate.get("query_frequency", ""),
                "period": candidate.get("query_period", ""),
            },
            "connectors": candidate.get("required_data_connectors", []),
            "source_tables": tables,
            "field_usage": fields,
            "mapped_oci_sources": mapped_sources,
            "missing_tables": missing_tables,
            "missing_fields": missing_fields,
            "hit_counts_by_lookback": candidate.get("hit_counts_by_lookback", {}),
            "stored_log_volume_bytes": int(candidate.get("stored_log_volume_bytes", 0) or 0),
            "retention_days": int(candidate.get("retention_days", 0) or 0),
            "dashboard_references": candidate.get("dashboard_references", []),
            "feed_dependencies": feed_dependencies,
            "migration_status": _status_for(blockers),
            "blockers": blockers,
        })

    return {
        "version": "1.0",
        "generated_at": utc_now(),
        "platform": "microsoft_sentinel",
        "source": source,
        "summary": {
            "content_count": len(items),
            "enabled_count": sum(1 for item in items if item["enabled"]),
            "blocked_count": sum(1 for item in items if item["blockers"]),
            "ready_for_local_validation_count": sum(1 for item in items if not item["blockers"]),
            "top_source_tables": dict(table_counts.most_common(20)),
            "blocker_counts": dict(sorted(blocker_counts.items())),
            "feed_dependency_count": sum(len(item["feed_dependencies"]) for item in items),
        },
        "items": items,
    }


def _load_candidates(path: Path, source_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if path.exists():
        payload = _read_json(path)
        return payload.get("candidates", []), payload.get("source", {})
    commit = resolve_sentinel_commit(source_dir)
    candidates = load_sentinel_candidates(source_dir, commit=commit)
    export = build_candidate_export(candidates, commit=commit)
    _write_json(path, export)
    return candidates, export.get("source", {})


def azure_inventory(input_path: Path) -> dict[str, Any]:
    payload = _read_json(input_path)
    raw_items = payload.get("items") or payload.get("rules") or payload.get("workbooks") or payload
    if not isinstance(raw_items, list):
        raise ValueError("Azure discovery input must be a list or contain items/rules/workbooks")
    source = payload.get("source", {"name": "Azure Log Analytics offline discovery"}) if isinstance(payload, dict) else {}
    candidates = []
    for index, item in enumerate(raw_items, start=1):
        query = str(item.get("query") or item.get("kql") or "")
        candidates.append({
            "sentinel_id": str(item.get("id") or item.get("content_id") or f"azure-offline-{index}"),
            "title": str(item.get("title") or item.get("name") or f"Azure content {index}"),
            "kind": str(item.get("kind") or item.get("content_kind") or "analytics_rule"),
            "query": query,
            "severity": str(item.get("severity") or "medium"),
            "enabled": bool(item.get("enabled", True)),
            "query_frequency": item.get("query_frequency") or item.get("frequency", ""),
            "query_period": item.get("query_period") or item.get("period", ""),
            "required_data_connectors": item.get("connectors", []),
            "source_path": item.get("source_path", ""),
            "source_url": item.get("source_url", ""),
            "hit_counts_by_lookback": item.get("hit_counts_by_lookback", {}),
            "stored_log_volume_bytes": item.get("stored_log_volume_bytes", 0),
            "retention_days": item.get("retention_days", 0),
            "dashboard_references": item.get("dashboard_references", []),
        })
    inventory = sentinel_inventory(candidates, source)
    inventory["platform"] = "azure_log_analytics"
    return inventory


def _priority_score(item: dict[str, Any]) -> int:
    score = 0
    if item.get("enabled"):
        score += 1000
    severity = str(item.get("severity", "medium")).lower()
    score += {"critical": 500, "high": 350, "medium": 150, "low": 50}.get(severity, 100)
    hit_counts = item.get("hit_counts_by_lookback", {})
    score += min(sum(int(value or 0) for value in hit_counts.values()), 500)
    score += min(int(item.get("stored_log_volume_bytes", 0) or 0) // 1_000_000, 250)
    score += 200 if item.get("dashboard_references") else 0
    score -= 300 * len(item.get("blockers", []))
    return score


def build_migration_plan(inventory: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    plan_items = []
    report_items = report.get("items", [])
    report_by_key = {
        (
            item.get("content_id", ""),
            item.get("source_path", ""),
            item.get("title", ""),
            item.get("kind", ""),
        ): item
        for item in report_items
    }
    for index, item in enumerate(inventory.get("items", [])):
        content_id = item.get("content_id", "")
        ready = item
        if index < len(report_items) and report_items[index].get("content_id", "") == content_id:
            ready = report_items[index]
        else:
            ready = report_by_key.get((
                content_id,
                item.get("source_path", ""),
                item.get("title", ""),
                item.get("kind", ""),
            ), item)
        blockers = ready.get("blockers", [])
        plan_items.append({
            "content_id": content_id,
            "title": item.get("title", ""),
            "kind": item.get("kind", ""),
            "priority_score": _priority_score(item),
            "enabled": item.get("enabled", False),
            "severity": item.get("severity", ""),
            "source_tables": item.get("source_tables", []),
            "mapped_oci_sources": ready.get("mapped_oci_sources", []),
            "feed_dependencies": item.get("feed_dependencies", []),
            "migration_status": ready.get("migration_status", ""),
            "blockers": blockers,
            "next_validation": (
                blockers[0].get("type", "unsupported")
                if blockers
                else "feed_staging" if item.get("feed_dependencies")
                else "local_validation"
            ),
        })
    plan_items.sort(key=lambda item: (-item["priority_score"], item["title"], item["content_id"]))
    return {
        "version": "1.0",
        "generated_at": utc_now(),
        "source_inventory": "queries/siem_discovery_inventory.json",
        "migration_report": report.get("report_path", ""),
        "summary": {
            "planned_count": len(plan_items),
            "ready_for_local_validation_count": sum(1 for item in plan_items if not item["blockers"]),
            "blocked_count": sum(1 for item in plan_items if item["blockers"]),
        },
        "items": plan_items,
    }


def migration_report(inventory: dict[str, Any]) -> dict[str, Any]:
    blocker_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    items = []
    for item in inventory.get("items", []):
        blockers = item.get("blockers", [])
        blocker_counts.update(blocker.get("type", "unsupported") for blocker in blockers)
        status_counts[item.get("migration_status", "unknown")] += 1
        classification = classify_next_query_candidate({
            "skip_reasons": [
                f"unsupported Sentinel field mapping: {field}" for field in item.get("missing_fields", [])
            ] + [
                f"unsupported Sentinel table: {table}" for table in item.get("missing_tables", [])
            ],
            "local_validation_errors": [],
            "live_validation_status": "not_run",
        })
        work_type = "table_mapping" if item.get("missing_tables") else classification["work_type"]
        if work_type not in BLOCKER_TYPES:
            work_type = "unsupported"
        items.append({
            **item,
            "blocker_type": work_type if blockers else "",
            "next_step": classification["next_step"] if blockers else "Run local conversion validation.",
            "priority_score": _priority_score(item),
        })
    return redact_sensitive_values({
        "version": "1.0",
        "generated_at": utc_now(),
        "inventory_generated_at": inventory.get("generated_at", ""),
        "platform": inventory.get("platform", ""),
        "summary": {
            "content_count": len(items),
            "ready_for_local_validation_count": sum(1 for item in items if not item.get("blockers")),
            "blocked_count": sum(1 for item in items if item.get("blockers")),
            "status_counts": dict(sorted(status_counts.items())),
            "blocker_counts": dict(sorted(blocker_counts.items())),
            "feed_dependency_count": sum(len(item.get("feed_dependencies", [])) for item in items),
        },
        "items": items,
    })


def command_sentinel(args: argparse.Namespace) -> int:
    candidates, source = _load_candidates(Path(args.candidates_file), Path(args.source_dir))
    inventory = sentinel_inventory(candidates, source)
    inventory = redact_sensitive_values(inventory)
    validate_artifact_schema(inventory, DISCOVERY_SCHEMA)
    _write_json(Path(args.out), inventory)
    print(f"Wrote {len(inventory['items'])} Sentinel inventory items to {args.out}")
    return 0


def command_azure(args: argparse.Namespace) -> int:
    inventory = redact_sensitive_values(azure_inventory(Path(args.input)))
    validate_artifact_schema(inventory, DISCOVERY_SCHEMA)
    _write_json(Path(args.out), inventory)
    print(f"Wrote {len(inventory['items'])} Azure inventory items to {args.out}")
    return 0


def command_report(args: argparse.Namespace) -> int:
    inventory_path = Path(args.inventory)
    inventory = _read_json(inventory_path)
    report = migration_report(inventory)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = Path(args.out) if args.out else DEFAULT_REPORT_DIR / f"siem-migration-{timestamp}.json"
    report["report_path"] = str(out_path.relative_to(PROJECT_DIR) if out_path.is_relative_to(PROJECT_DIR) else out_path)
    validate_artifact_schema(report, MIGRATION_REPORT_SCHEMA)
    _write_json(out_path, report)
    if args.plan_out:
        plan = build_migration_plan(inventory, report)
        validate_artifact_schema(plan, MIGRATION_PLAN_SCHEMA)
        _write_json(Path(args.plan_out), plan)
    print(f"Wrote SIEM migration report to {out_path}")
    return 0 if report["summary"]["blocked_count"] == 0 or args.report_only else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sentinel = sub.add_parser("sentinel", help="Build discovery inventory from Sentinel candidate intake")
    sentinel.add_argument("--candidates-file", default=str(DEFAULT_CANDIDATES_FILE))
    sentinel.add_argument("--source-dir", default=str(PROJECT_DIR / ".sentinel" / "Azure-Sentinel"))
    sentinel.add_argument("--out", default=str(DEFAULT_INVENTORY_PATH))
    sentinel.set_defaults(func=command_sentinel)

    azure = sub.add_parser("azure", help="Build discovery inventory from offline Azure workspace export")
    azure.add_argument("--input", required=True)
    azure.add_argument("--out", default=str(DEFAULT_INVENTORY_PATH))
    azure.set_defaults(func=command_azure)

    report = sub.add_parser("report", help="Build migration readiness report from a discovery inventory")
    report.add_argument("--inventory", default=str(DEFAULT_INVENTORY_PATH))
    report.add_argument("--out")
    report.add_argument("--plan-out", default=str(DEFAULT_MIGRATION_PLAN))
    report.add_argument("--report-only", action="store_true", help="Do not fail when blockers remain")
    report.set_defaults(func=command_report)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
