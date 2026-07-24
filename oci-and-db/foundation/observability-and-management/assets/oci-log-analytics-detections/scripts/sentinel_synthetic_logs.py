#!/usr/bin/env python3
"""Plan, generate, upload, and live-check Sentinel synthetic log batches.

The conversion pipeline only promotes Sentinel queries after live OCI parser
validation. This helper builds the data side of that loop: for each converted
candidate it derives the Logan fields used by the query, finds an existing
OCI parser/source contract that can supply those fields, emits a representative
NDJSON row, and records precise parser/source gaps when the contract is missing.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from convert_sentinel_kql import (  # noqa: E402
    ConversionResult,
    _clean_output_dir,
    _write_query_payload,
    build_conversion_report,
    convert_candidate,
    load_mapping_config,
    select_top_candidates,
    slugify_title,
)
from field_dictionary import (  # noqa: E402
    APPROVED_BUILTINS,
    _default_parser_definitions,
    extract_query_fields,
)
from oci_config import (  # noqa: E402
    LOG_GROUP_ID,
    ensure_log_group,
    get_la_client,
    get_namespace,
    list_available_log_sources,
    resolve_compartment_id,
    resolve_source_from_candidates,
)

PROJECT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CANDIDATES_FILE = PROJECT_DIR / "queries" / "sentinel_candidates.json"
DEFAULT_PLAN_PATH = PROJECT_DIR / "queries" / "sentinel_synthetic_plan.json"
DEFAULT_LIVE_RESULTS_PATH = PROJECT_DIR / "queries" / "sentinel_synthetic_live_results.json"
DEFAULT_SENTINEL_OUTPUT_DIR = PROJECT_DIR / "queries" / "sentinel"
DEFAULT_CONVERSION_REPORT_PATH = PROJECT_DIR / "queries" / "sentinel_conversion_report.json"
DEFAULT_DATA_DIR = PROJECT_DIR / "test_data" / "sentinel_synthetic"
DEFAULT_DICTIONARY_PATH = PROJECT_DIR / "queries" / "log_source_field_dictionary.json"

RUNTIME_FIELDS = {
    "Count",
    "Log Source",
    "Original Log Content",
    "Time",
    "msg",
    "time",
}
OCI_GAP_STEPS = [
    "confirm OCI source",
    "define parser or parser mapping",
    "define fields and aliases",
    "ingest representative sample logs",
    "validate in CAP tenancy",
    "update field dictionary",
    "add allow-list mapping",
    "add converter tests",
]
OCID_RE = re.compile(r"\bocid1\.[A-Za-z0-9_.-]+\b")
OCI_ENDPOINT_RE = re.compile(r"https://[A-Za-z0-9.-]+\.oci\.oraclecloud\.com[^\s'\")]*")
OCI_HOST_RE = re.compile(r"\b[A-Za-z0-9.-]+\.oci\.oraclecloud\.com\b")
NAMESPACE_PATH_RE = re.compile(r"/namespaces/[^/\s'\")]+")


def _safe_live_error(error: object, limit: int = 500) -> str:
    """Return a compact live-error string without OCI tenancy identifiers."""
    text = re.sub(r"\s+", " ", str(error)).strip()
    text = OCID_RE.sub("<OCI_OCID>", text)
    text = OCI_ENDPOINT_RE.sub("https://<OCI_ENDPOINT>", text)
    text = OCI_HOST_RE.sub("<OCI_ENDPOINT_HOST>", text)
    text = NAMESPACE_PATH_RE.sub("/namespaces/<OCI_NAMESPACE>", text)
    text = re.sub(r"opc-request-id[=:]\s*[^,\s]+", "opc-request-id=<REDACTED>", text, flags=re.IGNORECASE)
    return text[:limit]


@dataclass(frozen=True)
class SourceContract:
    """Existing parser/source contract details for one OCI Log Analytics source."""

    source_display: str
    parser_name: str
    parser_display: str
    field_paths: dict[str, list[str]]
    example: dict[str, Any]


def _read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_candidates(path: Path = DEFAULT_CANDIDATES_FILE) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Load normalized Microsoft Sentinel candidates."""
    payload = _read_json(path)
    return payload.get("candidates", []), payload.get("source", {})


def load_source_contracts() -> dict[str, SourceContract]:
    """Return parser contracts keyed by OCI Log Analytics source display name."""
    contracts: dict[str, SourceContract] = {}
    for definition in _default_parser_definitions():
        source_display = definition["source_display"]
        field_paths: dict[str, list[str]] = defaultdict(list)
        for field_name, json_path, _sequence in definition["field_mappings"]:
            if json_path not in field_paths[field_name]:
                field_paths[field_name].append(json_path)
        contracts[source_display] = SourceContract(
            source_display=source_display,
            parser_name=definition["parser_name"],
            parser_display=definition["parser_display"],
            field_paths=dict(field_paths),
            example=deepcopy(definition.get("example", {})),
        )
    return contracts


def _iter_single_quoted_values(text: str):
    in_quote = False
    escaped = False
    value: list[str] = []
    start = 0
    for index, char in enumerate(text):
        if escaped:
            value.append(char)
            escaped = False
            continue
        if char == "\\" and in_quote:
            value.append(char)
            escaped = True
            continue
        if char == "'":
            if in_quote:
                yield "".join(value), start, index + 1
                value = []
                in_quote = False
            else:
                in_quote = True
                start = index
            continue
        if in_quote:
            value.append(char)


def _strip_single_quoted_literals(text: str) -> str:
    output = []
    last = 0
    for _value, start, end in _iter_single_quoted_values(text):
        output.append(text[last:start])
        output.append("''")
        last = end
    output.append(text[last:])
    return "".join(output)


def extract_query_sources(query: str) -> list[str]:
    """Extract source names from the generated Logan Log Source filter."""
    return sorted(set(re.findall(r"'Log Source'\s*=\s*'((?:\\'|[^'])*)'", query)))


def extract_unquoted_operator_fields(query: str) -> set[str]:
    """Return unquoted fields used in simple Logan operator expressions."""
    stripped = _strip_single_quoted_literals(query)
    fields = set()
    pattern = re.compile(
        r"\b(?P<field>[A-Za-z_][A-Za-z0-9_]*)\s*(?:=|!=|>=|<=|>|<|\blike\b|\bnot\s+like\b|\bin\b|\bnot\s+in\b|\bis\b)",
        re.IGNORECASE,
    )
    command_words = {
        "and",
        "as",
        "by",
        "count",
        "eval",
        "fields",
        "head",
        "in",
        "not",
        "or",
        "sort",
        "stats",
        "where",
    }
    for match in pattern.finditer(stripped):
        field = match.group("field")
        if field.lower() not in command_words:
            fields.add(field)
    return fields


def extract_query_aliases(query: str) -> set[str]:
    """Return runtime aliases created by Logan pipeline stages."""
    aliases = set(re.findall(r"\bas\s+([A-Za-z_][A-Za-z0-9_]*)\b", query, flags=re.IGNORECASE))
    aliases.update(re.findall(r"\|\s*eval\s+([A-Za-z_][A-Za-z0-9_]*)\s*=", query, flags=re.IGNORECASE))
    return aliases


def extract_required_fields(query: str) -> set[str]:
    """Return OCI display fields that synthetic logs must populate."""
    fields = set(extract_query_fields(query))
    fields.update(extract_unquoted_operator_fields(query))
    fields.difference_update(extract_query_aliases(query))
    fields.difference_update(RUNTIME_FIELDS)
    return fields


def _unquote_field(raw: str) -> str:
    value = raw.strip()
    if len(value) >= 2 and value[0] == "'" and value[-1] == "'":
        return value[1:-1].replace("\\'", "'")
    return value


def _unquote_value(raw: str) -> Any:
    value = raw.strip()
    if len(value) >= 2 and value[0] == "'" and value[-1] == "'":
        return value[1:-1].replace("\\'", "'").replace("\\\\", "\\")
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?\d+\.\d+", value):
        return float(value)
    if value.lower() == "null":
        return None
    return value


def _default_value_for_field(field_name: str) -> Any:
    lowered = field_name.lower()
    if "ip" in lowered or "address" in lowered:
        return "198.51.100.42"
    if "port" in lowered:
        return 443
    if "status" in lowered:
        return "Failure"
    if "action" in lowered:
        return "blocked"
    if "url" in lowered:
        return "/sentinel/synthetic/payload"
    if "user" in lowered or "account" in lowered:
        return "sentinel.synthetic@example.com"
    if "host" in lowered or "computer" in lowered:
        return "sentinel-synth-01"
    if "command" in lowered:
        return "cmd.exe /c whoami"
    if "process" in lowered or "image" in lowered:
        return "cmd.exe"
    if "event id" in lowered:
        return "4688"
    if "time" in lowered:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return f"sentinel-{slugify_title(field_name)[:32]}"


def _match_value_for_operator(operator: str, raw_value: str) -> Any:
    value = _unquote_value(raw_value)
    if isinstance(value, str):
        value = value.replace("\\'", "'").replace("\\\\", "\\")
    if operator.lower() in {"!=", "not like"}:
        if value in {"Success", "success", "0"}:
            return "Failure"
        if value in {None, ""}:
            return "sentinel-value"
        return f"{value}-other"
    if operator.lower() == "like":
        text = str(value).replace("*", "").strip()
        return text or "sentinel-value"
    if operator in {">", ">="} and isinstance(value, (int, float)):
        return value + 1
    if operator in {"<", "<="} and isinstance(value, (int, float)):
        return value - 1
    return value


def _merge_predicate_value(existing: Any, new_value: Any) -> Any:
    """Combine repeated positive predicates for the same synthetic field."""
    if existing in {None, "", "sentinel-value"}:
        return new_value
    if new_value in {None, ""}:
        return existing
    if isinstance(existing, str) and isinstance(new_value, str):
        if new_value in existing:
            return existing
        return f"{existing} {new_value}".strip()
    return existing


def _should_merge_predicate(query: str, previous_end: int | None, current_start: int) -> bool:
    """Return false when repeated field predicates are disjunctive alternatives."""
    if previous_end is None:
        return True
    if current_start < previous_end:
        return False
    connector = _strip_single_quoted_literals(query[previous_end:current_start]).lower()
    return not re.search(r"\bor\b", connector)


def extract_predicate_values(query: str) -> dict[str, Any]:
    """Derive representative field values from simple Logan predicates."""
    values: dict[str, Any] = {}
    last_field_end: dict[str, int] = {}
    field_token = r"(?:'(?P<quoted>(?:\\'|[^'])+)'|(?P<bare>[A-Za-z_][A-Za-z0-9_]*))"
    value_token = r"(?:'(?P<value>(?:\\'|[^'])*)'|(?P<raw>-?\d+(?:\.\d+)?|null))"

    in_pattern = re.compile(
        rf"{field_token}\s+(?P<op>in|not\s+in)\s*\((?P<values>[^)]*)\)",
        re.IGNORECASE,
    )
    for match in in_pattern.finditer(query):
        field_name = _unquote_field(match.group("quoted") or match.group("bare") or "")
        if field_name == "Log Source":
            continue
        first_value = (match.group("values").split(",", 1)[0] or "").strip()
        if first_value:
            value = _unquote_value(first_value)
            if _should_merge_predicate(query, last_field_end.get(field_name), match.start()):
                values[field_name] = _merge_predicate_value(values.get(field_name), value)
            last_field_end[field_name] = match.end()

    comparison_pattern = re.compile(
        rf"{field_token}\s*(?P<op>=|!=|>=|<=|>|<|\blike\b|\bnot\s+like\b)\s*{value_token}",
        re.IGNORECASE,
    )
    for match in comparison_pattern.finditer(query):
        field_name = _unquote_field(match.group("quoted") or match.group("bare") or "")
        if field_name == "Log Source":
            continue
        raw_value = match.group("value") if match.group("value") is not None else match.group("raw")
        operator = match.group("op")
        if operator in {"!=", "not like"} and str(raw_value).strip().lower() in {"", "null"}:
            continue
        value = _match_value_for_operator(operator, str(raw_value))
        if operator in {"!=", "not like"} and field_name in values:
            continue
        if _should_merge_predicate(query, last_field_end.get(field_name), match.start()):
            values[field_name] = _merge_predicate_value(values.get(field_name), value)
        last_field_end[field_name] = match.end()
    return values


def choose_source_contract(
    sources: Iterable[str],
    required_fields: set[str],
    contracts: dict[str, SourceContract],
) -> tuple[SourceContract | None, list[str], list[str]]:
    """Pick the existing source contract with the best required-field coverage."""
    candidates = []
    missing_sources = []
    for source in sources:
        contract = contracts.get(source)
        if not contract:
            missing_sources.append(source)
            continue
        missing_fields = sorted(field for field in required_fields if field not in contract.field_paths)
        candidates.append((len(missing_fields), source, contract, missing_fields))
    if not candidates:
        return None, sorted(required_fields), sorted(missing_sources)
    _missing_count, _source, contract, missing_fields = sorted(candidates, key=lambda item: (item[0], item[1]))[0]
    return contract, missing_fields, sorted(missing_sources)


def _set_json_path(payload: dict[str, Any], json_path: str, value: Any) -> None:
    if not json_path.startswith("$."):
        return
    parts = json_path[2:].split(".")
    current = payload
    for part in parts[:-1]:
        nested = current.get(part)
        if not isinstance(nested, dict):
            nested = {}
            current[part] = nested
        current = nested
    current[parts[-1]] = value


def build_synthetic_event(
    contract: SourceContract,
    required_fields: set[str],
    predicate_values: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    """Build one parser-shaped NDJSON event for a converted Sentinel query."""
    event = deepcopy(contract.example)
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    event.setdefault("sentinelSynthetic", True)
    event.setdefault("sentinelId", candidate.get("sentinel_id", ""))
    event.setdefault("sentinelTitle", candidate.get("title", ""))
    for timestamp_field in (
        "@timestamp",
        "datetime",
        "eventTime",
        "time",
        "timeCreated",
        "timestamp",
        "TimeCreated",
        "Timestamp",
        "UtcTime",
    ):
        if timestamp_field in event or timestamp_field in {"timestamp", "TimeCreated", "Timestamp"}:
            event[timestamp_field] = timestamp
    for time_field in ("time", "Time"):
        for json_path in contract.field_paths.get(time_field, []):
            _set_json_path(event, json_path, timestamp)
    for field_name in sorted(required_fields):
        value = predicate_values.get(field_name, _default_value_for_field(field_name))
        for json_path in contract.field_paths.get(field_name, []):
            _set_json_path(event, json_path, value)
    return event


def _gap(reason: str, missing_fields: list[str], missing_sources: list[str]) -> dict[str, Any]:
    return {
        "reason": reason,
        "missing_fields": missing_fields,
        "missing_sources": missing_sources,
        "oci_steps": list(OCI_GAP_STEPS),
    }


def _progress_enabled(interval: float) -> bool:
    return interval >= 0


def _emit_progress(message: str, stream=None) -> None:
    print(f"[sentinel-synthetic] {message}", file=stream or sys.stderr, flush=True)


def build_synthetic_plan(
    *,
    top: int,
    candidates_file: Path = DEFAULT_CANDIDATES_FILE,
    data_dir: Path = DEFAULT_DATA_DIR,
    plan_path: Path = DEFAULT_PLAN_PATH,
    progress_interval: float = 30.0,
    progress_every: int = 100,
    progress_stream=None,
) -> dict[str, Any]:
    """Convert a batch and write synthetic NDJSON rows for parser-ready candidates."""
    candidates, source = load_candidates(candidates_file)
    mapping = load_mapping_config()
    contracts = load_source_contracts()
    selected = select_top_candidates(candidates, mapping, top=top)
    data_dir.mkdir(parents=True, exist_ok=True)

    started_at = time.monotonic()
    last_progress_at = started_at
    progress_every = max(1, int(progress_every))

    def maybe_progress(message: str, *, force: bool = False) -> None:
        nonlocal last_progress_at
        if not _progress_enabled(progress_interval):
            return
        now = time.monotonic()
        if force or progress_interval == 0 or now - last_progress_at >= progress_interval:
            _emit_progress(message, stream=progress_stream)
            last_progress_at = now

    maybe_progress(f"start top={top} selected={len(selected)} data_dir={data_dir}", force=True)

    rows_by_source_file: dict[str, list[dict[str, Any]]] = defaultdict(list)
    candidate_reports = []
    status_counts: Counter = Counter()

    for index, candidate in enumerate(selected, start=1):
        result = convert_candidate(candidate, mapping)
        context = f"{index}/{len(selected)} score={candidate.get('quality_score')} title=\"{candidate.get('title', '')[:96]}\""
        if not result.promoted_candidate:
            status_counts["conversion_skipped"] += 1
            candidate_reports.append({
                "title": candidate.get("title", ""),
                "sentinel_id": candidate.get("sentinel_id", ""),
                "quality_score": candidate.get("quality_score"),
                "source_path": candidate.get("source_path", ""),
                "status": "conversion_skipped",
                "skip_reasons": result.skip_reasons,
                "local_validation_errors": result.local_validation_errors,
            })
            maybe_progress(f"skip {context} reason=\"{(result.skip_reasons or result.local_validation_errors or [''])[0]}\"")
            continue

        query_payload = result.query_payload or {}
        query = query_payload.get("query", "")
        sources = extract_query_sources(query)
        required_fields = extract_required_fields(query)
        predicate_values = extract_predicate_values(query)
        contract, missing_fields, missing_sources = choose_source_contract(sources, required_fields, contracts)

        if not contract:
            status_counts["source_gap"] += 1
            candidate_reports.append({
                "title": candidate.get("title", ""),
                "sentinel_id": candidate.get("sentinel_id", ""),
                "quality_score": candidate.get("quality_score"),
                "source_path": candidate.get("source_path", ""),
                "status": "source_gap",
                "query": query,
                "sources": sources,
                "required_fields": sorted(required_fields),
                "gap": _gap("no existing parser/source contract for candidate sources", sorted(required_fields), missing_sources),
            })
            maybe_progress(f"source-gap {context} sources={','.join(sources)}")
            continue

        if missing_fields:
            status_counts["field_gap"] += 1
            candidate_reports.append({
                "title": candidate.get("title", ""),
                "sentinel_id": candidate.get("sentinel_id", ""),
                "quality_score": candidate.get("quality_score"),
                "source_path": candidate.get("source_path", ""),
                "status": "field_gap",
                "query": query,
                "selected_source": contract.source_display,
                "parser": contract.parser_display,
                "sources": sources,
                "required_fields": sorted(required_fields),
                "gap": _gap("selected parser does not expose every query field", missing_fields, missing_sources),
            })
            maybe_progress(f"field-gap {context} source=\"{contract.source_display}\" missing={len(missing_fields)}")
            continue

        event = build_synthetic_event(contract, required_fields, predicate_values, candidate)
        source_slug = slugify_title(contract.source_display)
        synthetic_file = f"{source_slug}.jsonl"
        rows_by_source_file[synthetic_file].append(event)
        status_counts["synthetic_ready"] += 1
        candidate_reports.append({
            "title": candidate.get("title", ""),
            "sentinel_id": candidate.get("sentinel_id", ""),
            "quality_score": candidate.get("quality_score"),
            "source_path": candidate.get("source_path", ""),
            "status": "synthetic_ready",
            "query": query,
            "selected_source": contract.source_display,
            "parser": contract.parser_display,
            "sources": sources,
            "required_fields": sorted(required_fields),
            "synthetic_file": synthetic_file,
        })
        maybe_progress(
            f"ready {context} source=\"{contract.source_display}\" fields={len(required_fields)}",
            force=progress_interval == 0 or index % progress_every == 0,
        )

    manifest_files = []
    for filename, rows in sorted(rows_by_source_file.items()):
        path = data_dir / filename
        path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
        manifest_files.append({"filename": filename, "events": len(rows)})

    manifest = {
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "files": manifest_files,
    }
    (data_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    report = {
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "summary": {
            "selected_candidates": len(selected),
            "synthetic_ready": status_counts["synthetic_ready"],
            "conversion_skipped": status_counts["conversion_skipped"],
            "source_gaps": status_counts["source_gap"],
            "field_gaps": status_counts["field_gap"],
            "data_dir": str(data_dir.relative_to(PROJECT_DIR) if data_dir.is_relative_to(PROJECT_DIR) else data_dir),
        },
        "files": manifest_files,
        "candidates": candidate_reports,
    }
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    maybe_progress(
        (
            f"complete ready={status_counts['synthetic_ready']} "
            f"source_gaps={status_counts['source_gap']} field_gaps={status_counts['field_gap']} "
            f"skipped={status_counts['conversion_skipped']} elapsed={int(time.monotonic() - started_at)}s "
            f"plan={plan_path}"
        ),
        force=True,
    )
    return report


def _upload_file(la_client, namespace: str, log_group_id: str, file_path: Path, source_name: str) -> dict[str, Any]:
    with file_path.open("rb") as handle:
        body = io.BytesIO(handle.read())
    response = la_client.upload_log_file(
        namespace_name=namespace,
        upload_name=f"sentinel-synthetic-{file_path.stem}",
        log_source_name=source_name,
        filename=file_path.name,
        opc_meta_loggrpid=log_group_id,
        upload_log_file_body=body,
        content_type="application/octet-stream",
        char_encoding="UTF-8",
    )
    return {
        "filename": file_path.name,
        "source": source_name,
        "status": response.status,
    }


def upload_synthetic_plan(plan_path: Path, data_dir: Path, dry_run: bool = False) -> dict[str, Any]:
    """Upload generated synthetic files using their selected source contracts."""
    plan = _read_json(plan_path)
    ready_by_file: dict[str, set[str]] = defaultdict(set)
    for candidate in plan.get("candidates", []):
        if candidate.get("status") == "synthetic_ready" and candidate.get("synthetic_file"):
            ready_by_file[candidate["synthetic_file"]].add(candidate.get("selected_source", ""))

    if dry_run:
        return {
            "dry_run": True,
            "files": [
                {"filename": filename, "sources": sorted(sources)}
                for filename, sources in sorted(ready_by_file.items())
            ],
        }

    _emit_progress("upload-stage client")
    try:
        la_client = get_la_client(timeout=(10, 60))
    except Exception as exc:
        return {"dry_run": False, "stage": "client", "ok": False, "error": _safe_live_error(exc), "uploads": []}

    _emit_progress("upload-stage namespace")
    try:
        namespace = get_namespace(la_client)
    except Exception as exc:
        return {"dry_run": False, "stage": "namespace", "ok": False, "error": _safe_live_error(exc), "uploads": []}

    _emit_progress("upload-stage log-group")
    try:
        log_group_id = LOG_GROUP_ID or ensure_log_group(la_client, namespace)
    except Exception as exc:
        return {"dry_run": False, "stage": "log_group", "ok": False, "error": _safe_live_error(exc), "uploads": []}

    _emit_progress("upload-stage source-discovery")
    try:
        available_sources = list_available_log_sources(la_client, namespace, resolve_compartment_id())
    except Exception as exc:
        return {"dry_run": False, "stage": "source_discovery", "ok": False, "error": _safe_live_error(exc), "uploads": []}

    uploads = []
    for filename, sources in sorted(ready_by_file.items()):
        source_candidates = sorted(source for source in sources if source)
        resolved_source = resolve_source_from_candidates(available_sources, source_candidates)
        if not resolved_source:
            uploads.append({
                "filename": filename,
                "ok": False,
                "error": f"none of the candidate sources exist in OCI: {source_candidates}",
            })
            continue
        file_path = data_dir / filename
        try:
            _emit_progress(f"upload-file filename={filename} source=\"{resolved_source}\"")
            outcome = _upload_file(la_client, namespace, log_group_id, file_path, resolved_source)
            uploads.append({**outcome, "ok": True})
        except Exception as exc:
            uploads.append({"filename": filename, "source": resolved_source, "ok": False, "error": _safe_live_error(exc)})
    return {"dry_run": False, "stage": "upload", "ok": all(item.get("ok") for item in uploads), "uploads": uploads}


def validate_live_plan(
    plan_path: Path,
    *,
    lookback: str,
    timeout: int,
    limit: int,
) -> dict[str, Any]:
    """Run live OCI validation for synthetic-ready candidates in a plan."""
    from deploy_dashboard import resolve_validation_namespace, validate_query_in_oci_isolated

    plan = _read_json(plan_path)
    ready = [candidate for candidate in plan.get("candidates", []) if candidate.get("status") == "synthetic_ready"]
    if limit > 0:
        ready = ready[:limit]
    namespace = resolve_validation_namespace(timeout)
    results = []
    for index, candidate in enumerate(ready, start=1):
        query_file = f"sentinel/{slugify_title(candidate.get('title', 'sentinel-query'))}.json"
        _emit_progress(f"live-start {index}/{len(ready)} title=\"{candidate.get('title', '')[:96]}\"")
        started_at = time.monotonic()
        result = validate_query_in_oci_isolated(
            namespace=namespace,
            query_file=query_file,
            query_string=candidate.get("query", ""),
            lookback=lookback,
            query_timeout=timeout,
        )
        results.append({
            "title": candidate.get("title", ""),
            "sentinel_id": candidate.get("sentinel_id", ""),
            "source_path": candidate.get("source_path", ""),
            "selected_source": candidate.get("selected_source", ""),
            "ok": bool(result.get("ok")),
            "rows": result.get("rows", 0),
            "empty": result.get("empty", False),
            "error": result.get("error", ""),
            "duration_seconds": round(time.monotonic() - started_at, 2),
        })
        _emit_progress(
            f"live-done {index}/{len(ready)} ok={bool(result.get('ok'))} rows={result.get('rows', 0)}"
        )
    return {
        "lookback": lookback,
        "timeout": timeout,
        "tested": len(results),
        "passed": sum(1 for result in results if result["ok"] and not result["empty"]),
        "empty": sum(1 for result in results if result["ok"] and result["empty"]),
        "failed": sum(1 for result in results if not result["ok"]),
        "results": results,
    }


def _candidate_key(item: dict[str, Any]) -> tuple[str, str]:
    return (str(item.get("sentinel_id", "")), str(item.get("source_path", "")))


def _live_result_key(item: dict[str, Any]) -> tuple[str, str]:
    return (str(item.get("sentinel_id", "")), str(item.get("source_path", "")))


def promote_live_results(
    *,
    plan_path: Path,
    live_results_path: Path,
    candidates_file: Path,
    output_dir: Path,
    report_path: Path,
    clean_output: bool = False,
) -> dict[str, Any]:
    """Write only non-empty live-passing synthetic plan items as promoted queries."""
    plan = _read_json(plan_path)
    live_results = _read_json(live_results_path)
    candidates, source = load_candidates(candidates_file)
    mapping = load_mapping_config()
    candidates_by_key = {_candidate_key(candidate): candidate for candidate in candidates}
    live_by_key = {_live_result_key(item): item for item in live_results.get("results", [])}
    plan_candidates = plan.get("candidates", [])

    if clean_output:
        _clean_output_dir(output_dir)

    results: list[ConversionResult] = []
    promoted_files = []
    for plan_candidate in plan_candidates:
        key = _candidate_key(plan_candidate)
        original = candidates_by_key.get(key)
        if not original:
            results.append(ConversionResult(plan_candidate, None, ["candidate not found in candidates file"], []))
            continue

        conversion = convert_candidate(original, mapping)
        live_result = live_by_key.get(key)
        if not conversion.promoted_candidate:
            results.append(conversion)
            continue

        if not live_result:
            results.append(ConversionResult(
                candidate=conversion.candidate,
                query_payload=conversion.query_payload,
                skip_reasons=["synthetic live validation not run"],
                local_validation_errors=conversion.local_validation_errors,
                live_validation_result={"ok": False, "rows": 0, "empty": False, "error": "synthetic live validation not run"},
            ))
            continue

        live_ok_with_rows = bool(live_result.get("ok")) and int(live_result.get("rows", 0)) > 0
        payload = {
            **(conversion.query_payload or {}),
            "live_validation_status": "passed" if live_ok_with_rows else "failed",
            "test_data_coverage": "synthetic_live_hit" if live_ok_with_rows else "synthetic_live_miss",
        }
        validation_result = {
            "ok": live_ok_with_rows,
            "rows": int(live_result.get("rows", 0)),
            "empty": bool(live_result.get("empty", False)),
            "error": live_result.get("error", ""),
        }
        if not live_ok_with_rows:
            results.append(ConversionResult(
                candidate=conversion.candidate,
                query_payload=payload,
                skip_reasons=["synthetic live validation did not return rows"],
                local_validation_errors=conversion.local_validation_errors,
                live_validation_result=validation_result,
            ))
            continue

        output_file = _write_query_payload(output_dir, payload)
        promoted_files.append(output_file)
        results.append(ConversionResult(
            candidate=conversion.candidate,
            query_payload=payload,
            skip_reasons=[],
            local_validation_errors=conversion.local_validation_errors,
            live_validation_result=validation_result,
            output_file=output_file,
        ))

    report = build_conversion_report(
        candidates=candidates,
        attempted=plan_candidates,
        results=results,
        source=source,
        validate_live=True,
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return {
        "promoted": len(promoted_files),
        "promoted_files": promoted_files,
        "report": str(report_path),
        "output_dir": str(output_dir),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate and validate synthetic logs for converted Sentinel KQL.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan = subparsers.add_parser("plan", help="Build synthetic logs and parser/source gap report.")
    plan.add_argument("--top", type=int, default=25, help="Top quality-ranked Sentinel candidates to attempt.")
    plan.add_argument("--candidates-file", default=str(DEFAULT_CANDIDATES_FILE))
    plan.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    plan.add_argument("--out", default=str(DEFAULT_PLAN_PATH))
    plan.add_argument("--progress-interval", type=float, default=30.0)
    plan.add_argument("--progress-every", type=int, default=100)

    upload = subparsers.add_parser("upload", help="Upload synthetic files from a generated plan.")
    upload.add_argument("--plan", default=str(DEFAULT_PLAN_PATH))
    upload.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    upload.add_argument("--dry-run", action="store_true")

    live = subparsers.add_parser("validate-live", help="Run live OCI validation for synthetic-ready plan items.")
    live.add_argument("--plan", default=str(DEFAULT_PLAN_PATH))
    live.add_argument("--out", default=str(DEFAULT_LIVE_RESULTS_PATH))
    live.add_argument("--lookback", default="24h")
    live.add_argument("--timeout", type=int, default=60)
    live.add_argument("--limit", type=int, default=5, help="Maximum ready candidates to validate; 0 means all.")

    promote = subparsers.add_parser("promote-validated", help="Promote only non-empty live-passing synthetic plan items.")
    promote.add_argument("--plan", default=str(DEFAULT_PLAN_PATH))
    promote.add_argument("--live-results", default=str(DEFAULT_LIVE_RESULTS_PATH))
    promote.add_argument("--candidates-file", default=str(DEFAULT_CANDIDATES_FILE))
    promote.add_argument("--output-dir", default=str(DEFAULT_SENTINEL_OUTPUT_DIR))
    promote.add_argument("--report", default=str(DEFAULT_CONVERSION_REPORT_PATH))
    promote.add_argument("--clean-output", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "plan":
        report = build_synthetic_plan(
            top=args.top,
            candidates_file=Path(args.candidates_file),
            data_dir=Path(args.data_dir),
            plan_path=Path(args.out),
            progress_interval=args.progress_interval,
            progress_every=args.progress_every,
        )
        print(json.dumps(report["summary"], indent=2))
        return 0
    if args.command == "upload":
        result = upload_synthetic_plan(Path(args.plan), Path(args.data_dir), dry_run=args.dry_run)
        print(json.dumps(result, indent=2))
        failed = [item for item in result.get("uploads", []) if not item.get("ok")]
        return 1 if failed else 0
    if args.command == "validate-live":
        result = validate_live_plan(
            Path(args.plan),
            lookback=args.lookback,
            timeout=args.timeout,
            limit=args.limit,
        )
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))
        return 1 if result["failed"] else 0
    if args.command == "promote-validated":
        result = promote_live_results(
            plan_path=Path(args.plan),
            live_results_path=Path(args.live_results),
            candidates_file=Path(args.candidates_file),
            output_dir=Path(args.output_dir),
            report_path=Path(args.report),
            clean_output=args.clean_output,
        )
        print(json.dumps(result, indent=2))
        return 0
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
