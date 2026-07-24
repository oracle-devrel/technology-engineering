#!/usr/bin/env python3
"""Convert supported Microsoft Sentinel KQL into OCI Log Analytics Logan QL.

Facade module — public API enumerated in ``__all__`` (D-15). Phase 6 keeps
the full implementation here; plans 06-02..06-09 extract operator helpers
into ``scripts/kql/operators/<op>.py``; plan 06-10 reduces this file to
<=800 lines.
"""

from __future__ import annotations

__all__ = [
    "ConversionResult",
    "_clean_output_dir",
    "_write_query_payload",
    "build_conversion_report",
    "classify_unsupported_kql",
    "convert_candidate",
    "convert_candidates",
    "convert_kql_to_logan",
    "apply_discovery_evidence",
    "apply_mapping_profile",
    "load_mapping_config",
    "load_mapping_profile",
    "rank_candidates",
    "select_top_candidates",
    "slugify_title",
    "validate_logan_query_local",
    # Phase 6 transitional re-exports — new callers should import from
    # ``scripts.kql.canonical`` / ``scripts.kql.types`` directly.
    "canonical",
    "CanonicalizationError",
    "Tier",
]

import argparse
import concurrent.futures
import json
import os
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# Make every entry point work — direct script run (``python scripts/convert_sentinel_kql.py``)
# only puts ``scripts/`` on sys.path; ``-m scripts.convert_sentinel_kql`` puts the project
# root on sys.path. Add both so the absolute ``scripts.*`` imports below resolve in either case.
_FACADE_PATH = Path(__file__).resolve()
_SCRIPTS_DIR = _FACADE_PATH.parent
_PROJECT_ROOT = _SCRIPTS_DIR.parent
for _candidate in (_PROJECT_ROOT, _SCRIPTS_DIR):
    if str(_candidate) not in sys.path:
        sys.path.insert(0, str(_candidate))

from scripts.sync_sentinel_kql import (  # noqa: E402,F401 — re-exported for legacy callers
    DEFAULT_CACHE_DIR,
    SENTINEL_LICENSE_URL,
    SENTINEL_WEB_URL,
    build_candidate_export,
    load_sentinel_candidates,
    resolve_sentinel_commit,
    sync_sentinel_repo,
)

from scripts.kql._facade_impl import (  # noqa: E402,F401
    AZURE_AUDIT_SCHEMA_FIELDS,
    CONFIG_PATH,
    ConversionResult,
    DEFAULT_CANDIDATES_FILE,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REPORT_PATH,
    ENTITY_ENRICHMENT_ALIASES,
    ENTITY_ENRICHMENT_ALIASES_NORMALIZED,
    FIELD_DICTIONARY_PATH,
    LOGAN_BUILTIN_FIELDS,
    LOGAN_COMMANDS,
    LOGAN_UNSUPPORTED_PATTERNS,
    NUMERIC_FIELD_TYPES,
    PROJECT_DIR,
    SEVERITY_SCORE,
    STRING_FIELD_TYPES,
    SUPPORTED_AGGREGATIONS,
    UNSUPPORTED_PATTERNS,
    _classify_unsupported_kql_text,
    _cleanup_boolean_expression,
    _convert_extend,
    _convert_fields_clause,
    _convert_sort,
    _convert_summarize,
    _convert_top,
    _default_aggregate_alias,
    _display_field_name,
    _escape_logan_string,
    _extract_query_aliases,
    _extract_query_field_references,
    _extract_unquoted_operator_fields,
    _field_is_quoted,
    _find_top_level_semicolon,
    _format_value,
    _format_value_for_field,
    _is_allowed_logan_field,
    _iter_quoted_values,
    _literal_value,
    _load_field_dictionary_field_types,
    _load_field_dictionary_fields,
    _logan_field_reference,
    _normalize_field_name,
    _normalize_simple_let_expression,
    _preprocess_simple_lets,
    _quote_context_indicates_field,
    _record_field_error,
    _remove_time_filters,
    _replace_unquoted_variables,
    _sanitize_alias,
    _split_alias_expression,
    _split_kql_stages,
    _split_top_level,
    _strip_kql_comments,
    _strip_single_quoted_literals,
    _strip_string_literals,
    _unique_alias,
    _clean_table_name,
    _source_filter_for_tables,
    classify_unsupported_kql,
    convert_kql_to_logan,
    convert_predicate,
    extract_source_tables,
    load_mapping_config,
    map_field,
    validate_logan_query_local,
)
from scripts.redaction import redact_text  # noqa: E402
from scripts.sentinel_profiles import (  # noqa: E402,F401
    DEFAULT_PROFILE_NAME,
    apply_discovery_evidence,
    apply_mapping_profile,
    build_migration_plan_from_report,
    load_mapping_profile,
)

def slugify_title(title: str) -> str:
    """Create a stable filesystem-safe slug."""
    slug = re.sub(r"[^a-z0-9_-]+", "_", title.lower()).strip("_")
    return slug[:96] or "sentinel_query"


def _reference_entries(candidate: dict) -> list[dict]:
    references = []
    if candidate.get("source_url"):
        references.append({"name": "Microsoft Sentinel source rule", "url": candidate["source_url"]})
    references.append({"name": "Microsoft Sentinel repository", "url": SENTINEL_WEB_URL})
    references.append({"name": "Azure/Azure-Sentinel license", "url": SENTINEL_LICENSE_URL})
    return references


def _dashboard_metadata(query: str) -> dict:
    # Aggregated queries (stats / timestats / eventstats) must NOT use a plain
    # `table` viz: OCI's dashboard records-companion appends `| fields ID`/`Time`
    # which is invalid after an aggregation and errors at render time. Use
    # `summary_table`, which renders the aggregated rollup without that append.
    aggregated = any(tok in query for tok in ("| stats ", "| timestats", "| eventstats"))
    visualization = "summary_table" if aggregated else "table"
    return {
        "visualizationType": visualization,
        "timeSelection": {"timePeriod": "l21d"},
        "ask_ai_prompts": [
            "Summarize the Microsoft Sentinel converted detection results and identify the highest-risk pivots."
        ],
    }


def build_query_payload(candidate: dict, query: str, source_info: dict, live_validation_status: str) -> dict:
    """Build a saved-search JSON payload for one promoted Sentinel conversion."""
    level = candidate.get("severity", "medium")
    return {
        "title": candidate.get("title", "Microsoft Sentinel Converted Detection"),
        "description": candidate.get("description", ""),
        "query": query,
        "level": level,
        "source_type": "microsoft_sentinel",
        "sentinel_id": candidate.get("sentinel_id", ""),
        "sentinel_source_path": candidate.get("source_path", ""),
        "sentinel_source_url": candidate.get("source_url", ""),
        "required_data_connectors": candidate.get("required_data_connectors", []),
        "conversion_status": "promoted",
        "conversion_confidence": "medium",
        "source_confidence": "high",
        "live_validation_status": live_validation_status,
        "sentinel_tables": source_info.get("tables", []),
        "sentinel_category": source_info.get("category", "unknown"),
        "tags": ["microsoft_sentinel", f"sentinel.{source_info.get('category', 'unknown')}"],
        "mitre_attack": candidate.get("mitre_attack", {"tactics": [], "techniques": []}),
        "logsource": {
            "product": "microsoft_sentinel",
            "service": source_info.get("service", "unknown"),
            "candidates": source_info.get("sources", []),
            "original_tables": source_info.get("tables", []),
        },
        "references": _reference_entries(candidate),
        "attribution": candidate.get("attribution", {
            "source": "Microsoft Sentinel",
            "repository": "Azure/Azure-Sentinel",
            "license": "MIT",
            "license_url": SENTINEL_LICENSE_URL,
        }),
        "dashboard": _dashboard_metadata(query),
        "detection_maturity": "source_converted",
        "field_coverage": "mapped_subset",
        "test_data_coverage": "not_evaluated",
        "scheduled_rule_eligibility": "not_evaluated",
    }


def convert_candidate(candidate: dict, mapping: dict, live_validation_status: str = "not_run") -> ConversionResult:
    """Convert one Sentinel candidate, returning skip reasons on failure."""
    query, source_info, errors = convert_kql_to_logan(candidate.get("query", ""), mapping)
    if errors:
        return ConversionResult(candidate, None, errors, [])

    local_errors = validate_logan_query_local(query)
    payload = build_query_payload(candidate, query, source_info, live_validation_status)
    return ConversionResult(candidate, payload, [], local_errors)


def rank_candidate(candidate: dict, mapping: dict) -> int:
    """Quality-first candidate scoring."""
    score = SEVERITY_SCORE.get(str(candidate.get("severity", "medium")).lower(), 20)
    score += int(candidate.get("discovery_evidence_score", 0) or 0)
    if candidate.get("description"):
        score += min(len(candidate["description"]) // 80, 10)
    mitre = candidate.get("mitre_attack", {})
    score += len(mitre.get("tactics", [])) * 5
    score += len(mitre.get("techniques", [])) * 5
    if candidate.get("required_data_connectors"):
        score += 8
    if candidate.get("kind") == "analytics_rule":
        score += 5

    unsupported = classify_unsupported_kql(candidate.get("query", ""))
    if unsupported:
        score -= 1000
    tables = extract_source_tables(candidate.get("query", ""))
    if tables and all(table in mapping["tables"] for table in tables):
        score += 20
    else:
        score -= 300
    if len(candidate.get("query", "")) > 5000:
        score -= 25
    return score


def rank_candidates(candidates: list[dict], mapping: dict) -> list[dict]:
    """Return candidates sorted by deterministic quality score."""
    ranked = []
    for candidate in candidates:
        ranked.append({**candidate, "quality_score": rank_candidate(candidate, mapping)})
    return sorted(
        ranked,
        key=lambda item: (
            -item["quality_score"],
            item.get("source_path", ""),
            item.get("sentinel_id", ""),
        ),
    )


def select_top_candidates(candidates: list[dict], mapping: dict, top: int = 1000) -> list[dict]:
    """Select the top N quality-ranked candidates."""
    return rank_candidates(candidates, mapping)[:top]


def _load_candidates_from_file(path: Path) -> tuple[list[dict], dict]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return payload.get("candidates", []), payload.get("source", {})


def _validate_live(query_file: str, query: str, lookback: str, timeout: int) -> dict:
    from deploy_dashboard import validate_query_in_oci_isolated, resolve_validation_namespace

    namespace = resolve_validation_namespace(timeout)
    return validate_query_in_oci_isolated(
        namespace=namespace,
        query_file=query_file,
        query_string=query,
        lookback=lookback,
        query_timeout=timeout,
    )


def _progress_value(value: object, limit: int = 120) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _format_elapsed(seconds: float) -> str:
    seconds = max(0, int(seconds))
    minutes, second = divmod(seconds, 60)
    hours, minute = divmod(minutes, 60)
    if hours:
        return f"{hours}h{minute:02d}m{second:02d}s"
    if minute:
        return f"{minute}m{second:02d}s"
    return f"{second}s"


def _conversion_status_label(result: ConversionResult, output_file: str = "") -> str:
    if output_file:
        return "promoted"
    if result.live_validation_result and not result.live_validation_result.get("ok"):
        return "live_failed"
    if result.promoted_candidate:
        return "converted"
    if result.local_validation_errors:
        return "local_failed"
    return "skipped"


def _progress_reason(result: ConversionResult) -> str:
    if result.live_validation_result and result.live_validation_result.get("error"):
        return _safe_progress_error(result.live_validation_result.get("error", ""))
    reasons = result.skip_reasons or result.local_validation_errors
    return _progress_value(reasons[0], limit=140) if reasons else ""


def _safe_progress_error(error: object) -> str:
    text = _progress_value(error, limit=180)
    text = re.sub(r"['\"]?opc-request-id['\"]?\s*:\s*['\"][^'\"]+['\"],?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bopc-request-id\b[=:]\s*[^,\s]+", "", text, flags=re.IGNORECASE)
    return _progress_value(text, limit=140)


def _progress_context(candidate: dict, index: int, total: int) -> str:
    score = candidate.get("quality_score", "n/a")
    title = _progress_value(candidate.get("title", ""), limit=96)
    source_path = _progress_value(candidate.get("source_path", ""), limit=96)
    return f"{index}/{total} score={score} title=\"{title}\" source=\"{source_path}\""


def _emit_progress(stream, message: str) -> None:
    print(f"[sentinel-convert] {message}", file=stream, flush=True)


def _write_query_payload(output_dir: Path, payload: dict) -> str:
    base = slugify_title(payload["title"])
    filename = f"{base}.json"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    if output_path.exists():
        try:
            existing = json.loads(output_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            existing = {}
        same_source_rule = (
            existing.get("sentinel_id") == payload.get("sentinel_id")
            and existing.get("sentinel_source_path") == payload.get("sentinel_source_path")
        )
        if not same_source_rule:
            suffix = slugify_title(str(payload.get("sentinel_id") or payload.get("sentinel_source_path") or "sentinel"))[:24]
            filename = f"{base}_{suffix}.json"
            output_path = output_dir / filename
            counter = 2
            while output_path.exists():
                filename = f"{base}_{suffix}_{counter}.json"
                output_path = output_dir / filename
                counter += 1
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return f"sentinel/{filename}"


def _clean_output_dir(output_dir: Path) -> None:
    if not output_dir.exists():
        return
    for path in output_dir.glob("*.json"):
        path.unlink()


def _tier_for_result(result: "ConversionResult") -> str:
    """Phase 6 tier classifier (D-16).

    PR-1 default — tier-3 when the converter flagged skip reasons or local
    validation errors, otherwise tier-1. tier-2 is reserved for transforms
    with a documented rewrite; operator extractions (06-02..06-09) populate
    that bucket once they emit ``StageResult.tier``.
    """

    if result.skip_reasons or result.local_validation_errors:
        return "tier_3"
    return "tier_1"


def build_conversion_report(
    candidates: list[dict],
    attempted: list[dict],
    results: list[ConversionResult],
    source: dict,
    validate_live: bool,
    profile: dict | None = None,
) -> dict:
    """Build the Sentinel conversion report artifact."""
    unsupported_counts = Counter()
    for result in results:
        for reason in result.skip_reasons + result.local_validation_errors:
            unsupported_counts[reason] += 1

    promoted = [result for result in results if result.output_file]
    converted = [result for result in results if result.promoted_candidate]
    skipped = [
        result for result in results
        if result.skip_reasons or result.local_validation_errors
    ]
    live_passed = [
        result for result in results
        if result.live_validation_result and result.live_validation_result.get("ok")
    ]
    live_failed = [
        result for result in results
        if result.live_validation_result and not result.live_validation_result.get("ok")
    ]

    tier_distribution = {"tier_1": 0, "tier_2": 0, "tier_3": 0}
    result_tiers: list[str] = []
    for result in results:
        tier_key = _tier_for_result(result)
        tier_distribution[tier_key] += 1
        result_tiers.append(tier_key)

    return {
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": source or {
            "name": "Microsoft Sentinel",
            "repository": SENTINEL_WEB_URL,
            "license": "MIT",
            "license_url": SENTINEL_LICENSE_URL,
        },
        "runtime_profile": profile or {},
        "summary": {
            "total_candidates": len(candidates),
            "attempted_candidates": len(attempted),
            "promoted_count": len(promoted),
            "converted_count": len(converted),
            "skipped_count": len(skipped),
            "ranking": "quality-first",
            "live_validation_requested": validate_live,
            "live_validation_passed": len(live_passed),
            "live_validation_failed": len(live_failed),
            "tier_distribution": tier_distribution,
        },
        "unsupported_features": dict(sorted(unsupported_counts.items())),
        "attempted": [
            {
                "sentinel_id": result.candidate.get("sentinel_id", ""),
                "title": result.candidate.get("title", ""),
                "quality_score": result.candidate.get("quality_score"),
                "discovery_evidence_score": result.candidate.get("discovery_evidence_score", 0),
                "discovery_hit_counts_by_lookback": result.candidate.get("discovery_hit_counts_by_lookback", {}),
                "discovery_dashboard_references": result.candidate.get("discovery_dashboard_references", []),
                "source_path": result.candidate.get("source_path", ""),
                "source_url": result.candidate.get("source_url", ""),
                "conversion_status": (
                    "promoted" if result.output_file
                    else "converted_not_written" if result.promoted_candidate
                    else "skipped"
                ),
                "output_file": result.output_file,
                "skip_reasons": result.skip_reasons,
                "local_validation_errors": result.local_validation_errors,
                "tier": tier,
                "live_validation_status": (
                    "passed" if result.live_validation_result and result.live_validation_result.get("ok")
                    else "failed" if result.live_validation_result
                    else "not_run"
                ),
                "live_validation_error": (
                    redact_text(result.live_validation_result.get("error", ""))
                    if result.live_validation_result else ""
                ),
            }
            for result, tier in zip(results, result_tiers)
        ],
    }


def convert_candidates(
    candidates: list[dict],
    mapping: dict,
    top: int = 1000,
    validate_live: bool = False,
    write_working: bool = False,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report_path: Path = DEFAULT_REPORT_PATH,
    source: dict | None = None,
    lookback: str = "24h",
    timeout: int = 60,
    clean_output: bool = False,
    progress_interval: float = 30.0,
    progress_every: int = 100,
    progress_stream=None,
    profile: dict | None = None,
    workers: int = 1,
) -> dict:
    """Rank, convert, optionally live-validate, and optionally write queries."""
    attempted = select_top_candidates(candidates, mapping, top=top)
    if write_working and clean_output:
        _clean_output_dir(output_dir)

    progress_enabled = progress_interval >= 0
    progress_stream = progress_stream or sys.stderr
    progress_every = max(1, int(progress_every))
    started_at = time.monotonic()
    last_progress_at = started_at
    counters: Counter = Counter()

    def maybe_progress(message: str, *, force: bool = False) -> None:
        nonlocal last_progress_at
        if not progress_enabled:
            return
        now = time.monotonic()
        if force or progress_interval == 0 or now - last_progress_at >= progress_interval:
            _emit_progress(progress_stream, message)
            last_progress_at = now

    maybe_progress(
        (
            f"start total_candidates={len(candidates)} attempted={len(attempted)} "
            f"live_validation={validate_live} write_working={write_working} timeout={timeout}s"
        ),
        force=True,
    )

    # ── Phase 1 (parallel) ────────────────────────────────────────────────────
    # Run pure-CPU convert_candidate() for every candidate in bounded threads.
    # No network calls, no shared mutable state: mapping is read-only, and
    # ConversionResult is a frozen dataclass.  Results are keyed by original
    # position so Phase 2 can retrieve them in a stable, deterministic order.
    # workers=1 leaves _parallel_pre empty, activating the unchanged serial path.
    _parallel_pre: dict[int, ConversionResult | Exception] = {}
    if workers > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_idx = {
                executor.submit(convert_candidate, candidate, mapping): idx
                for idx, candidate in enumerate(attempted)
            }
            for future in concurrent.futures.as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    _parallel_pre[idx] = future.result()
                except Exception as exc:  # noqa: BLE001 — record, don't crash the pool
                    _parallel_pre[idx] = exc

    # ── Phase 2 (serial, ordered) ─────────────────────────────────────────────
    # Live OCI validation, file writes, counters, and progress all run here
    # in original candidate order.  When _parallel_pre is populated we retrieve
    # the pre-computed result; otherwise the unchanged serial path executes.
    results: list[ConversionResult] = []
    total_attempted = len(attempted)
    for index, candidate in enumerate(attempted, start=1):
        context = _progress_context(candidate, index, total_attempted)
        if not validate_live:
            maybe_progress(f"candidate-start {context}", force=index == 1)

        if _parallel_pre:
            raw = _parallel_pre[index - 1]
            result = (
                ConversionResult(candidate, None, [f"conversion error: {raw}"], [])
                if isinstance(raw, Exception)
                else raw
            )
        else:
            result = convert_candidate(candidate, mapping)
        if result.promoted_candidate and validate_live:
            tentative_file = f"sentinel/{slugify_title(result.query_payload['title'])}.json"
            maybe_progress(f"live-start {context} query_file=\"{tentative_file}\"", force=True)
            live_started_at = time.monotonic()
            live_result = _validate_live(tentative_file, result.query_payload["query"], lookback, timeout)
            live_status = "passed" if live_result.get("ok") else "failed"
            payload = {**result.query_payload, "live_validation_status": live_status}
            result = ConversionResult(
                candidate=result.candidate,
                query_payload=payload,
                skip_reasons=[] if live_result.get("ok") else ["live OCI validation failed"],
                local_validation_errors=result.local_validation_errors,
                live_validation_result=live_result,
            )
            duration = _format_elapsed(time.monotonic() - live_started_at)
            live_reason = _safe_progress_error(live_result.get("error", "")) if not live_result.get("ok") else ""
            reason_text = f" reason=\"{live_reason}\"" if live_reason else ""
            maybe_progress(f"live-{live_status} {context} duration={duration}{reason_text}", force=True)

        output_file = ""
        if write_working and result.promoted_candidate:
            output_file = _write_query_payload(output_dir, result.query_payload)
        if output_file:
            result = ConversionResult(
                candidate=result.candidate,
                query_payload=result.query_payload,
                skip_reasons=result.skip_reasons,
                local_validation_errors=result.local_validation_errors,
                live_validation_result=result.live_validation_result,
                output_file=output_file,
            )
        results.append(result)

        status = _conversion_status_label(result, output_file=output_file)
        counters[status] += 1
        if result.live_validation_result and result.live_validation_result.get("ok"):
            counters["live_passed"] += 1
        elif result.live_validation_result and status != "live_failed":
            counters["live_failed"] += 1
        reason = _progress_reason(result)
        reason_text = f" reason=\"{reason}\"" if reason else ""
        maybe_progress(
            (
                f"candidate-done {context} status={status}{reason_text} "
                f"converted={counters['converted']} promoted={counters['promoted']} "
                f"skipped={counters['skipped']} local_failed={counters['local_failed']} "
                f"live_failed={counters['live_failed']}"
            ),
            force=progress_interval == 0 or index % progress_every == 0 or index == total_attempted,
        )

    report = build_conversion_report(
        candidates=candidates,
        attempted=attempted,
        results=results,
        source=source or {},
        validate_live=validate_live,
        profile=profile,
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    maybe_progress(
        (
            f"complete attempted={total_attempted} converted={report['summary']['converted_count']} "
            f"promoted={report['summary']['promoted_count']} skipped={report['summary']['skipped_count']} "
            f"live_passed={report['summary']['live_validation_passed']} "
            f"live_failed={report['summary']['live_validation_failed']} "
            f"elapsed={_format_elapsed(time.monotonic() - started_at)} report=\"{report_path}\""
        ),
        force=True,
    )
    return report


def _ensure_candidates(args) -> tuple[list[dict], dict]:
    candidates_path = Path(args.candidates_file)
    if candidates_path.exists():
        return _load_candidates_from_file(candidates_path)

    cache_dir = Path(args.source_dir)
    if not args.no_sync:
        commit = sync_sentinel_repo(cache_dir=cache_dir, ref=args.ref, refresh=args.refresh)
    else:
        commit = resolve_sentinel_commit(cache_dir)
        if not cache_dir.exists():
            raise FileNotFoundError(f"Sentinel checkout not found: {cache_dir}")

    candidates = load_sentinel_candidates(cache_dir, commit=commit)
    export = build_candidate_export(candidates, commit=commit)
    candidates_path.parent.mkdir(parents=True, exist_ok=True)
    candidates_path.write_text(json.dumps(export, indent=2) + "\n", encoding="utf-8")
    return candidates, export["source"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert Microsoft Sentinel KQL to Logan QL")
    parser.add_argument("--top", type=int, default=1000, help="Number of quality-ranked candidates to attempt")
    parser.add_argument("--validate-local", action="store_true", help="Run local conversion validation")
    parser.add_argument("--validate-live", action="store_true", help="Run live OCI Log Analytics parser validation")
    parser.add_argument("--write-working", action="store_true", help="Write converted queries that pass validation")
    parser.add_argument(
        "--allow-local-write",
        action="store_true",
        help="Allow writing local-only conversions without live validation",
    )
    parser.add_argument("--clean-output", action="store_true", help="Clean queries/sentinel/*.json before writing")
    parser.add_argument("--candidates-file", default=str(DEFAULT_CANDIDATES_FILE))
    parser.add_argument("--source-dir", default=str(DEFAULT_CACHE_DIR), help="Sentinel repo cache directory")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT_PATH))
    parser.add_argument("--profile", default=DEFAULT_PROFILE_NAME, help="Runtime mapping profile name or YAML path")
    parser.add_argument("--discovery-report", default="", help="Optional SIEM discovery inventory/report for ranking evidence")
    parser.add_argument("--migration-plan-out", default="", help="Optional migration plan JSON output path")
    parser.add_argument("--ref", default="master", help="Sentinel git ref for auto-sync")
    parser.add_argument("--refresh", action="store_true", help="Fetch remote changes during auto-sync")
    parser.add_argument("--no-sync", action="store_true", help="Do not fetch if candidates file is missing")
    parser.add_argument("--query-lookback", default="24h", help="Lookback window for live validation")
    parser.add_argument("--query-timeout", type=int, default=60, help="Per-query live validation timeout")
    parser.add_argument(
        "--progress-interval",
        type=float,
        default=30.0,
        help="Seconds between periodic progress lines; set 0 for every candidate, -1 to disable.",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=100,
        help="Emit a candidate progress line at least every N attempted candidates.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=min(8, os.cpu_count() or 1),
        help=(
            "Parallel conversion worker threads for the CPU-bound convert_candidate phase. "
            "1 = serial (exact original path). Default: min(8, cpu_count)."
        ),
    )
    args = parser.parse_args()

    if args.write_working and not args.validate_live and not args.allow_local_write:
        parser.error("--write-working requires --validate-live unless --allow-local-write is supplied")

    profile = load_mapping_profile(args.profile)
    mapping = apply_mapping_profile(load_mapping_config(), profile)
    candidates, source = _ensure_candidates(args)
    candidates = apply_discovery_evidence(
        candidates,
        Path(args.discovery_report) if args.discovery_report else None,
    )
    report = convert_candidates(
        candidates=candidates,
        mapping=mapping,
        top=args.top,
        validate_live=args.validate_live,
        write_working=args.write_working,
        output_dir=Path(args.output_dir),
        report_path=Path(args.report),
        source=source,
        lookback=args.query_lookback,
        timeout=args.query_timeout,
        clean_output=args.clean_output,
        progress_interval=args.progress_interval,
        progress_every=args.progress_every,
        profile=profile,
        workers=args.workers,
    )
    if args.migration_plan_out:
        build_migration_plan_from_report(report, Path(args.migration_plan_out))

    summary = report["summary"]
    print("Microsoft Sentinel conversion")
    print(f"  Profile:    {profile.get('name', args.profile)}")
    print(f"  Candidates: {summary['total_candidates']}")
    print(f"  Attempted:  {summary['attempted_candidates']}")
    print(f"  Converted:  {summary['converted_count']}")
    print(f"  Promoted:   {summary['promoted_count']}")
    print(f"  Skipped:    {summary['skipped_count']}")
    print(f"  Report:     {Path(args.report)}")
    return 0


# Phase 6 transitional re-exports. Import at the bottom to avoid pulling the
# kql subpackage during this module's top-of-file execution (which is where
# legacy helpers used by the subpackage are defined).
from scripts.kql.canonical import (  # noqa: E402,F401
    CanonicalizationError,
    canonical,
)
from scripts.kql.types import Tier  # noqa: E402,F401

if __name__ == "__main__":
    raise SystemExit(main())
