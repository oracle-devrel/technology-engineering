#!/usr/bin/env python3
"""Generate aggregate QL conversion capability data for Logan Forge.

The analyzer can inspect a local Elastic detection-rules checkout, but it only
emits aggregate counts and field/operator names. It intentionally does not write
third-party rule names, rule IDs, descriptions, notes, or query bodies.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "queries" / "ql_conversion_capability_matrix.json"

ELASTIC_REPO_URL = "https://github.com/elastic/detection-rules"
ELASTIC_LICENSE = "Elastic License v2"

SOURCE_CAPABILITIES: list[dict[str, Any]] = [
    {
        "language": "sigma_yaml",
        "label": "Sigma YAML",
        "status": "supported",
        "backend_entrypoint": "scripts/convert_sigma.py",
        "conversion_path": "structured_rule_to_logan",
        "next_capabilities": ["aggregation condition review", "field mapping expansion"],
    },
    {
        "language": "sentinel_kql",
        "label": "Microsoft Sentinel KQL",
        "status": "supported",
        "backend_entrypoint": "scripts/kql/_facade_impl.py",
        "conversion_path": "operator_pipeline_to_logan",
        "next_capabilities": ["Phase 9 operator parity", "MAP-05 field coverage"],
    },
    {
        "language": "splunk_spl",
        "label": "Splunk SPL",
        "status": "partial",
        "backend_entrypoint": "scripts/logan_workbench_convert.py",
        "conversion_path": "deterministic_pattern_mapping",
        "next_capabilities": ["SPL parser", "subsearch and lookup dependency modeling"],
    },
    {
        "language": "elastic_lucene",
        "label": "Elastic Lucene",
        "status": "partial",
        "backend_entrypoint": "scripts/logan_workbench_convert.py",
        "conversion_path": "ECS field pattern mapping",
        "next_capabilities": ["Lucene parser", "range/exists/regex parity"],
    },
    {
        "language": "elastic_kuery",
        "label": "Elastic Kuery / Kibana KQL",
        "status": "partial",
        "backend_entrypoint": "scripts/logan_workbench_convert.py",
        "conversion_path": "ECS field pattern mapping",
        "next_capabilities": ["Kuery parser", "nested boolean group support"],
    },
    {
        "language": "elastic_eql",
        "label": "Elastic EQL",
        "status": "partial",
        "backend_entrypoint": "scripts/logan_workbench_convert.py",
        "conversion_path": "single-event filters plus simple process sequence mapping",
        "next_capabilities": ["advanced sequence conditions", "sample and maxspan handling"],
    },
    {
        "language": "elastic_esql",
        "label": "Elastic ES|QL",
        "status": "partial",
        "backend_entrypoint": "scripts/logan_workbench_convert.py",
        "conversion_path": "pipeline_to_logan",
        "next_capabilities": ["advanced ES|QL functions", "enrich/mv_expand dependency modeling"],
    },
    {
        "language": "elastic_toml",
        "label": "Elastic detection TOML",
        "status": "partial",
        "backend_entrypoint": "scripts/logan_workbench_convert.py",
        "conversion_path": "metadata_dispatch_to_language_converter",
        "next_capabilities": ["rule type dispatch", "threshold/new_terms/threat_match metadata"],
    },
    {
        "language": "osquery_sql",
        "label": "OSQuery SQL",
        "status": "partial",
        "backend_entrypoint": "scripts/logan_workbench_convert.py",
        "conversion_path": "osquery_result_logs_to_logan",
        "next_capabilities": ["result-log conversion", "endpoint state unsupported reporting"],
    },
    {
        "language": "yara",
        "label": "YARA",
        "status": "partial",
        "backend_entrypoint": "scripts/logan_workbench_convert.py",
        "conversion_path": "yara_result_logs_to_logan",
        "next_capabilities": ["result-log conversion", "raw file scan unsupported reporting"],
    },
    {
        "language": "oci_logan",
        "label": "OCI Logan QL",
        "status": "supported",
        "backend_entrypoint": "scripts/logan_workbench_convert.py",
        "conversion_path": "validated_passthrough",
        "next_capabilities": ["syntax lint", "field dictionary validation"],
    },
]

OPERATOR_MARKERS = {
    "sequence": r"\bsequence\b",
    "sample": r"\bsample\b",
    "where": r"\bwhere\b",
    "stats": r"\bstats\b",
    "eval": r"\beval\b",
    "keep": r"\bkeep\b",
    "sort": r"\bsort\b",
    "limit": r"\blimit\b",
    "wildcard": r"[*?]",
    "regex": r"\b(regex|rlike|matches|like~?)\b",
    "in_list": r"\bin\s*\(",
    "cidr": r"\b(cidr_match|cidrmatch|cidr)\b",
    "lookup_or_enrich": r"\b(enrich|lookup)\b",
    "conditional": r"\b(case|if)\s*\(",
    "array_or_multivalue": r"\b(array|mv_|values|count_distinct)\b",
    "time_window": r"\b(now|ago|date_diff|@timestamp|timestamp)\b",
}

FIELD_RE = re.compile(r"(?<![A-Za-z0-9_@])(@timestamp|[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z0-9_@-]+)+)")
FIELD_PREFIXES = (
    "@timestamp",
    "agent.",
    "aws.",
    "azure.",
    "cloud.",
    "container.",
    "data_stream.",
    "destination.",
    "dns.",
    "event.",
    "file.",
    "host.",
    "http.",
    "network.",
    "o365.",
    "okta.",
    "process.",
    "registry.",
    "service.",
    "source.",
    "url.",
    "user.",
    "user_agent.",
)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_toml(text: str) -> dict[str, Any]:
    try:
        import tomllib  # type: ignore[attr-defined]
    except ModuleNotFoundError:
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ModuleNotFoundError:
            return parse_toml_fallback(text)
    try:
        return tomllib.loads(text)
    except Exception:
        return parse_toml_fallback(text)


def parse_toml_fallback(text: str) -> dict[str, Any]:
    """Best-effort TOML extraction for environments without a TOML parser."""
    rule_match = re.search(r"(?ms)^\[rule\]\s*(.*?)(?:^\[|\Z)", text)
    rule_text = rule_match.group(1) if rule_match else text
    query_match = re.search(r"(?ms)^query\s*=\s*'''(.*?)'''", rule_text)
    return {
        "rule": {
            "type": extract_scalar(rule_text, "type") or "<missing>",
            "language": extract_scalar(rule_text, "language") or "<none>",
            "query": query_match.group(1) if query_match else "",
        }
    }


def extract_scalar(text: str, key: str) -> str:
    match = re.search(rf"(?m)^{re.escape(key)}\s*=\s*\"([^\"]+)\"", text)
    return match.group(1) if match else ""


def git_value(repo: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            check=False,
            text=True,
            timeout=5,
        )
    except OSError:
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def counter_entries(counter: collections.Counter[str], limit: int | None = None) -> list[dict[str, Any]]:
    items = counter.most_common(limit)
    return [{"name": key, "count": count} for key, count in items]


def safe_query_text(rule: dict[str, Any]) -> str:
    query = rule.get("query", "")
    return query if isinstance(query, str) else ""


def scan_rule_file(path: Path) -> tuple[str, str, str]:
    data = load_toml(path.read_text(encoding="utf-8", errors="replace"))
    rule = data.get("rule", {}) if isinstance(data, dict) else {}
    rule_type = str(rule.get("type") or "<missing>")
    language = str(rule.get("language") or "<none>")
    return rule_type, language, safe_query_text(rule)


def scan_hunt_file(path: Path) -> tuple[tuple[str, ...], str]:
    data = load_toml(path.read_text(encoding="utf-8", errors="replace"))
    hunt = data.get("hunt", {}) if isinstance(data, dict) else {}
    languages = hunt.get("language") or data.get("language") or ["<missing>"]
    if isinstance(languages, str):
        languages = [languages]
    queries = hunt.get("query") or data.get("query") or []
    if isinstance(queries, str):
        queries = [queries]
    return tuple(str(language) for language in languages), "\n".join(str(query) for query in queries)


def collect_markers(query: str, markers: collections.Counter[str]) -> None:
    lowered = query.lower()
    for name, pattern in OPERATOR_MARKERS.items():
        if re.search(pattern, lowered):
            markers[name] += 1


def collect_fields(query: str, fields: collections.Counter[str]) -> None:
    seen = set()
    for token in FIELD_RE.findall(query):
        if token == "@timestamp" or token.startswith(FIELD_PREFIXES):
            seen.add(token)
    fields.update(seen)


def analyze_elastic_repo(repo: Path) -> dict[str, Any]:
    rules_dir = repo / "rules"
    building_block_dir = repo / "rules_building_block"
    hunting_dir = repo / "hunting"
    rule_files = list(rules_dir.rglob("*.toml")) if rules_dir.exists() else []
    rule_files.extend(list(building_block_dir.rglob("*.toml")) if building_block_dir.exists() else [])

    by_type: collections.Counter[str] = collections.Counter()
    by_language: collections.Counter[str] = collections.Counter()
    language_by_type: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    operator_markers: collections.Counter[str] = collections.Counter()
    field_refs: collections.Counter[str] = collections.Counter()

    for path in rule_files:
        rule_type, language, query = scan_rule_file(path)
        by_type[rule_type] += 1
        by_language[language] += 1
        language_by_type[rule_type][language] += 1
        collect_markers(query, operator_markers)
        collect_fields(query, field_refs)

    hunt_language: collections.Counter[str] = collections.Counter()
    hunt_markers: collections.Counter[str] = collections.Counter()
    hunt_files = list(hunting_dir.rglob("*.toml")) if hunting_dir.exists() else []
    for path in hunt_files:
        languages, query = scan_hunt_file(path)
        hunt_language.update(languages)
        collect_markers(query, hunt_markers)

    return {
        "source_repository": ELASTIC_REPO_URL,
        "source_ref": git_value(repo, "rev-parse", "--short", "HEAD"),
        "source_commit_date": git_value(repo, "log", "-1", "--format=%cI"),
        "license": {
            "name": ELASTIC_LICENSE,
            "policy": "aggregate_analysis_only_no_rule_content_committed",
            "project_doc": "docs/THIRD_PARTY_DETECTION_CONTENT.md",
        },
        "rules": {
            "total_files": len(rule_files),
            "by_type": counter_entries(by_type),
            "by_language": counter_entries(by_language),
            "language_by_type": {
                rule_type: counter_entries(counter) for rule_type, counter in sorted(language_by_type.items())
            },
            "operator_markers": counter_entries(operator_markers),
            "top_field_references": counter_entries(field_refs, 40),
        },
        "hunting": {
            "total_files": len(hunt_files),
            "by_language": counter_entries(hunt_language),
            "operator_markers": counter_entries(hunt_markers),
        },
        "content_exclusions": [
            "rule_names",
            "rule_ids",
            "descriptions",
            "notes",
            "query_bodies",
            "file_paths",
        ],
    }


def build_matrix(elastic_repo: Path | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": "1.0.0",
        "generated_at": now_iso(),
        "generated_by": "scripts/analyze_ql_conversion_coverage.py",
        "content_policy": {
            "third_party_rule_content": "excluded",
            "license_doc": "docs/THIRD_PARTY_DETECTION_CONTENT.md",
            "excluded_fields": [
                "query_bodies",
                "rule_names",
                "descriptions",
                "notes",
            ],
            "notes": [
                "Capability artifacts store aggregate support metadata only.",
                "Third-party rule text is converted only when supplied at request time.",
            ],
        },
        "source_capabilities": SOURCE_CAPABILITIES,
        "target_language": {
            "name": "OCI Log Analytics QL",
            "canonical_artifact": "queries/logan_ql_reference_catalog.json",
            "shared_ir_modules": ["scripts/ql/ir.py", "scripts/ql/logan_emit.py"],
        },
        "third_party_corpora": [],
    }
    if elastic_repo and elastic_repo.exists():
        payload["third_party_corpora"].append(analyze_elastic_repo(elastic_repo))
    else:
        payload["third_party_corpora"].append(
            {
                "source_repository": ELASTIC_REPO_URL,
                "license": {
                    "name": ELASTIC_LICENSE,
                    "policy": "aggregate_analysis_only_no_rule_content_committed",
                    "project_doc": "docs/THIRD_PARTY_DETECTION_CONTENT.md",
                },
                "status": "not_scanned",
                "reason": "Pass --elastic-repo /path/to/detection-rules to include aggregate counts.",
            }
        )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate QL conversion capability matrix")
    parser.add_argument("--elastic-repo", type=Path, help="Optional local elastic/detection-rules checkout")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--print-json", action="store_true", help="Write matrix to stdout instead of a file")
    args = parser.parse_args()

    payload = build_matrix(args.elastic_repo)
    serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.print_json:
        print(serialized, end="")
        return 0

    output = args.output if args.output.is_absolute() else PROJECT_ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialized)
    print(f"wrote {output.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
