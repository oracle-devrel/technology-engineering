#!/usr/bin/env python3
"""Generate parser/source/field dictionary artifacts for OCI Log Analytics content."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from oci_config import PROJECT_DIR, QUERIES_DIR, SOURCE_CANDIDATE_GROUPS
from query_artifacts import is_saved_search_query_file

OUTPUT_PATH = Path(QUERIES_DIR) / "log_source_field_dictionary.json"
CONTRACT_PATH = Path(PROJECT_DIR) / "config" / "synthetic_log_contracts.json"

RESERVED_FOR_CUSTOM_PARSERS = {
    "Original Log Content": "mbody",
    "mbody": "mbody",
}

APPROVED_BUILTINS = sorted({
    "Channel",
    "Count",
    "Entity",
    "Event Type",
    "Image",
    "Log Source",
    "Original Log Content",
    "Provider",
    "Resource Name",
    "Severity",
    "Status",
    "Time",
    "Type",
    "User",
    "User Name",
    "msg",
    "time",
})

FIELD_REFERENCE_RE = re.compile(r"'([^']+)'")
FIELD_OPERATOR_RE = re.compile(r"\s*(?:=|!=|>=|<=|>|<|\blike\b|\bnot\s+like\b|\bin\b|\bnot\s+in\b|\bis\b)", re.IGNORECASE)
OCID_RE = re.compile(r"\bocid1\.[A-Za-z0-9_.-]+\b")
IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
URL_RE = re.compile(r"\bhttps?://[^\s\"']+")


def sanitize_example_value(value: Any) -> Any:
    """Return variable-safe example values for public field dictionary output."""
    if isinstance(value, str):
        sanitized = URL_RE.sub("<URL>", value)
        sanitized = EMAIL_RE.sub("<USER_EMAIL>", sanitized)
        sanitized = OCID_RE.sub("<OCI_RESOURCE_OCID>", sanitized)
        sanitized = IPV4_RE.sub("<IP_ADDRESS>", sanitized)
        return sanitized
    if isinstance(value, list):
        return [sanitize_example_value(item) for item in value]
    if isinstance(value, dict):
        return {
            key: sanitize_example_value(nested_value)
            for key, nested_value in value.items()
        }
    return value


def _iter_quoted_values(text: str):
    """Yield single-quoted values while respecting backslash-escaped quotes."""
    in_quote = False
    escaped = False
    start = 0
    value: list[str] = []
    for index, char in enumerate(text):
        if escaped:
            value.append(char)
            escaped = False
            continue
        if char == "\\" and in_quote:
            escaped = True
            value.append(char)
            continue
        if char == "'":
            if in_quote:
                yield "".join(value), start, index + 1
                in_quote = False
                value = []
            else:
                in_quote = True
                start = index
                value = []
            continue
        if in_quote:
            value.append(char)


def _json_path_value(example: dict[str, Any], json_path: str) -> Any:
    if not json_path.startswith("$."):
        return None
    key = json_path[2:]
    if key in example:
        return example[key]
    current: Any = example
    for part in key.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _default_parser_definitions() -> list[dict[str, Any]]:
    import setup_log_sources as setup

    prefixes = [
        "LINUX",
        "WINDOWS",
        "CG",
        "CGIS",
        "WINSEC",
        "WINSYS",
        "WINPS",
        "WINDEF",
        "LINSEC",
        "SYSMON",
        "SYSNET",
        "WAF",
        "LB",
        "WEBAPP",
        "APP",
        "GENAI",
        "VCN",
        "FW",
        "HEALTH",
    ]
    definitions = []
    for prefix in prefixes:
        definitions.append({
            "parser_name": getattr(setup, f"{prefix}_PARSER_NAME"),
            "parser_display": getattr(setup, f"{prefix}_PARSER_DISPLAY"),
            "source_internal": getattr(setup, f"{prefix}_SOURCE_INTERNAL"),
            "source_display": getattr(setup, f"{prefix}_SOURCE_DISPLAY"),
            "field_mappings": getattr(setup, f"{prefix}_FIELD_MAPPINGS"),
            "example": getattr(setup, f"{prefix}_EXAMPLE"),
        })
    return definitions


def _field_type(field_name: str) -> str:
    import setup_log_sources as setup

    return setup.FIELD_DATA_TYPE_OVERRIDES.get(field_name, "STRING")


def _field_kind(field_name: str) -> str:
    if field_name in RESERVED_FOR_CUSTOM_PARSERS:
        return "reserved"
    if field_name in APPROVED_BUILTINS:
        return "built-in"
    return "custom"


def _load_contracts(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open() as f:
        return json.load(f)


def _load_query_payloads(queries_dir: Path = Path(QUERIES_DIR)) -> list[tuple[str, dict[str, Any]]]:
    payloads = []
    for path in sorted(queries_dir.rglob("*.json")):
        if not is_saved_search_query_file(path):
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and payload.get("query"):
            payloads.append((path.relative_to(queries_dir).as_posix(), payload))
    return payloads


def _quote_context_indicates_field(query: str, start: int, end: int) -> bool:
    after = query[end:]
    before = query[:start]
    if FIELD_OPERATOR_RE.match(after):
        return True
    tail = before[-32:].lower()
    return bool(re.search(r"\b(?:distinctcount|unique|count|sum|max|min|avg|average)\s*\($", tail))


def extract_query_fields(query: str) -> set[str]:
    """Extract quoted OCI LA field references from an OCL query string."""
    fields: set[str] = set()
    for value, start, end in _iter_quoted_values(query):
        if _quote_context_indicates_field(query, start, end):
            fields.add(value)
    for by_match in re.finditer(
        r"\|\s*(?:stats|timestats|eventstats|link)[^|]*\bby\b(?P<clause>[^|]+)",
        query,
        flags=re.IGNORECASE,
    ):
        fields.update(value for value, _start, _end in _iter_quoted_values(by_match.group("clause")))
    for fields_match in re.finditer(r"\|\s*fields\s+(?P<clause>[^|]+)", query, flags=re.IGNORECASE):
        fields.update(value for value, _start, _end in _iter_quoted_values(fields_match.group("clause")))
    return fields


def _contract_datasets_for_path(raw_key: str, contracts: dict[str, Any]) -> list[str]:
    datasets = []
    for dataset, contract in contracts.items():
        required = set(contract.get("required_fields", []))
        nested = set(contract.get("required_nested_fields", []))
        if raw_key in required or raw_key in nested:
            datasets.append(dataset)
    return sorted(datasets)


def build_field_dictionary(
    *,
    parser_definitions: list[dict[str, Any]] | None = None,
    source_candidate_groups: dict[str, list[str]] | None = None,
    query_payloads: list[tuple[str, dict[str, Any]]] | None = None,
    contracts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a field dictionary from parser mappings, contracts, and query usage."""
    parser_definitions = parser_definitions or _default_parser_definitions()
    source_candidate_groups = source_candidate_groups or SOURCE_CANDIDATE_GROUPS
    query_payloads = query_payloads if query_payloads is not None else _load_query_payloads()
    contracts = contracts if contracts is not None else _load_contracts()

    usage_by_field: dict[str, set[str]] = defaultdict(set)
    for rel_path, payload in query_payloads:
        for field in extract_query_fields(payload.get("query", "")):
            usage_by_field[field].add(rel_path)

    groups_by_source: dict[str, set[str]] = defaultdict(set)
    for group_name, sources in source_candidate_groups.items():
        for source in sources:
            groups_by_source[source].add(group_name)

    field_records: dict[str, dict[str, Any]] = {}
    parser_records = []
    source_records = []

    for definition in parser_definitions:
        parser_records.append({
            "parser_name": definition["parser_name"],
            "parser_display": definition["parser_display"],
            "source_internal": definition["source_internal"],
            "source_display": definition["source_display"],
            "field_count": len(definition["field_mappings"]),
        })
        source_records.append({
            "source_internal": definition["source_internal"],
            "source_display": definition["source_display"],
            "parser_name": definition["parser_name"],
            "candidate_groups": sorted(groups_by_source.get(definition["source_display"], set())),
        })

        for display_name, json_path, sequence in definition["field_mappings"]:
            raw_key = json_path[2:] if json_path.startswith("$.") else json_path
            value = _json_path_value(definition.get("example", {}), json_path)
            record = field_records.setdefault(display_name, {
                "display_name": display_name,
                "kind": _field_kind(display_name),
                "type": _field_type(display_name),
                "raw_json_paths": [],
                "parsers": [],
                "sources": [],
                "source_candidate_groups": [],
                "example_values": [],
                "contract_datasets": [],
                "queries_using_it": [],
                "dashboards_using_it": [],
                "reserved_backing_field": RESERVED_FOR_CUSTOM_PARSERS.get(display_name, ""),
            })
            if json_path not in record["raw_json_paths"]:
                record["raw_json_paths"].append(json_path)
            parser_entry = {
                "parser_name": definition["parser_name"],
                "parser_display": definition["parser_display"],
                "sequence": sequence,
                "raw_json_path": json_path,
            }
            if parser_entry not in record["parsers"]:
                record["parsers"].append(parser_entry)
            source_entry = {
                "source_internal": definition["source_internal"],
                "source_display": definition["source_display"],
            }
            if source_entry not in record["sources"]:
                record["sources"].append(source_entry)
            record["source_candidate_groups"] = sorted(
                set(record["source_candidate_groups"])
                | groups_by_source.get(definition["source_display"], set())
            )
            safe_value = sanitize_example_value(value)
            if safe_value is not None and str(safe_value) not in {str(existing) for existing in record["example_values"]}:
                record["example_values"].append(safe_value)
            record["contract_datasets"] = sorted(
                set(record["contract_datasets"]) | set(_contract_datasets_for_path(raw_key, contracts))
            )

    for field_name, paths in usage_by_field.items():
        if field_name in field_records:
            field_records[field_name]["queries_using_it"] = sorted(paths)

    fields = sorted(field_records.values(), key=lambda record: record["display_name"].lower())
    reserved_violations = [
        f"{parser['parser_display']} maps reserved field {field['display_name']}"
        for field in fields
        if field["display_name"] in RESERVED_FOR_CUSTOM_PARSERS
        for parser in field["parsers"]
    ]

    return {
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_fields": len(fields),
            "parser_count": len(parser_records),
            "source_count": len(source_records),
            "reserved_mapping_violations": len(reserved_violations),
            "fields_with_query_usage": sum(1 for field in fields if field["queries_using_it"]),
        },
        "approved_builtins": APPROVED_BUILTINS,
        "reserved_for_custom_parsers": RESERVED_FOR_CUSTOM_PARSERS,
        "source_candidate_groups": source_candidate_groups,
        "parsers": parser_records,
        "sources": source_records,
        "fields": fields,
        "validation": {
            "reserved_mapping_errors": reserved_violations,
        },
    }


def validate_field_dictionary(dictionary: dict[str, Any]) -> list[str]:
    """Validate dictionary-level invariants."""
    errors = list(dictionary.get("validation", {}).get("reserved_mapping_errors", []))
    seen = set()
    for field in dictionary.get("fields", []):
        name = field.get("display_name", "")
        if name in seen:
            errors.append(f"duplicate field dictionary entry: {name}")
        seen.add(name)
    return errors


def validate_query_field_coverage(
    relative_path: str,
    payload: dict[str, Any],
    dictionary: dict[str, Any],
) -> list[str]:
    """Validate that quoted query fields exist in the dictionary or approved built-ins."""
    known = {field.get("display_name", "") for field in dictionary.get("fields", [])}
    approved = set(dictionary.get("approved_builtins", APPROVED_BUILTINS))
    errors = []
    for field in sorted(extract_query_fields(payload.get("query", ""))):
        if field not in known and field not in approved:
            errors.append(f"{relative_path}: unknown query field '{field}'")
    return errors


def build_query_field_coverage_report(
    dictionary: dict[str, Any],
    query_payloads: list[tuple[str, dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Return machine-readable query field coverage for saved-search payloads."""
    query_payloads = query_payloads if query_payloads is not None else _load_query_payloads()
    known = {field.get("display_name", "") for field in dictionary.get("fields", [])}
    approved = set(dictionary.get("approved_builtins", APPROVED_BUILTINS))
    unknown_fields = []

    for relative_path, payload in query_payloads:
        for field in sorted(extract_query_fields(payload.get("query", ""))):
            if field not in known and field not in approved:
                unknown_fields.append({
                    "query_file": relative_path,
                    "field": field,
                })

    return {
        "ok": not unknown_fields,
        "total_query_files": len(query_payloads),
        "unknown_field_count": len(unknown_fields),
        "unknown_fields": unknown_fields,
    }


def validate_all_query_field_coverage(dictionary: dict[str, Any]) -> list[str]:
    report = build_query_field_coverage_report(dictionary)
    return [
        f"{item['query_file']}: unknown query field '{item['field']}'"
        for item in report["unknown_fields"]
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate OCI Log Analytics field dictionary")
    parser.add_argument("--out", default=str(OUTPUT_PATH), help="Output JSON path")
    parser.add_argument("--validate-query-fields", action="store_true", help="Fail if query fields are missing from the dictionary")
    args = parser.parse_args()

    dictionary = build_field_dictionary()
    errors = validate_field_dictionary(dictionary)
    if args.validate_query_fields:
        errors.extend(validate_all_query_field_coverage(dictionary))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(dictionary, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {dictionary['summary']['total_fields']} fields to {out_path}")

    if errors:
        print("Field dictionary validation errors:")
        for error in errors[:50]:
            print(f"  - {error}")
        if len(errors) > 50:
            print(f"  - ... {len(errors) - 50} more")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
