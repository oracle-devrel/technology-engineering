#!/usr/bin/env python3
"""Operator workflow wrapper for Microsoft Sentinel KQL conversion."""

from __future__ import annotations

import argparse
import ast
import html
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

# scripts/ is sys.path[0] when run directly; tests put scripts/ on the path too.
# obs_logging is a sibling module. Guard the import so importing this workflow in
# a context without scripts/ on the path degrades to a no-op logger rather than
# an ImportError.
try:
    from obs_logging import get_logger, bind  # noqa: E402
    log = get_logger("sentinel_conversion_workflow")
except ImportError:  # pragma: no cover - defensive
    import logging as _logging
    log = _logging.getLogger("sentinel_conversion_workflow")

    def bind(_logger, **_fields):  # type: ignore[misc]
        return _logger

PROJECT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CANDIDATES_FILE = PROJECT_DIR / "queries" / "sentinel_candidates.json"
DEFAULT_REPORT_PATH = PROJECT_DIR / "queries" / "sentinel_conversion_report.json"
DEFAULT_LOCAL_REPORT_PATH = Path("/tmp/sentinel_conversion_local.json")
DEFAULT_SENTINEL_DIR = PROJECT_DIR / "queries" / "sentinel"
DEFAULT_DASHBOARD_INVENTORY = PROJECT_DIR / "queries" / "dashboard_inventory.json"
DEFAULT_HTML_PATH = PROJECT_DIR / "docs" / "sentinel_converter.html"
DEFAULT_MIGRATION_PLAN = PROJECT_DIR / "queries" / "migration_plan_sentinel.json"
DEFAULT_PROFILE_NAME = "azure_as_is"
SENTINEL_DASHBOARD_PREFIX = "SOC: Microsoft Sentinel "
NEXT_QUERY_WORK_TYPES = {
    "live_environment": {
        "priority": 0,
        "guidance": (
            "Rerun live validation after OCI auth, tenancy, or clock-skew issues are fixed; do not edit "
            "the query before confirming the environment is healthy."
        ),
    },
    "live_validation": {
        "priority": 1,
        "guidance": (
            "Fix generated Logan QL or parser-field usage, then rerun live promotion. "
            "Do not write this candidate manually under queries/sentinel/."
        ),
    },
    "local_validation": {
        "priority": 2,
        "guidance": "Fix converter output so local guardrails pass before any live validation attempt.",
    },
    "field_mapping": {
        "priority": 3,
        "guidance": (
            "Verify the field exists in queries/log_source_field_dictionary.json or approved built-ins "
            "before extending config/sentinel_oci_mapping.yaml."
        ),
    },
    "table_mapping": {
        "priority": 4,
        "guidance": (
            "Add a Sentinel table/source mapping only when there is a real OCI Log Analytics source "
            "and parser-field contract."
        ),
    },
    "kql_support": {
        "priority": 5,
        "guidance": (
            "Add deterministic converter support only when Logan QL has equivalent semantics; otherwise "
            "leave the candidate skipped with a clear reason."
        ),
    },
    "unsupported": {
        "priority": 6,
        "guidance": "Keep skipped unless a real mapping or deterministic converter implementation is added.",
    },
}
NEXT_QUERY_STRATEGIES = {
    "default": [
        "live_environment",
        "live_validation",
        "local_validation",
        "field_mapping",
        "table_mapping",
        "kql_support",
        "unsupported",
    ],
    "foundational": [
        "field_mapping",
        "table_mapping",
        "kql_support",
        "local_validation",
        "live_validation",
        "live_environment",
        "unsupported",
    ],
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


def _project_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_DIR))
    except ValueError:
        return str(path)


def _read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def resolve_top(value: str, candidates_file: Path = DEFAULT_CANDIDATES_FILE) -> int:
    """Resolve --top, accepting either an integer or 'all'."""
    normalized = str(value).strip().lower()
    if normalized != "all":
        try:
            top = int(normalized)
        except ValueError as exc:
            raise argparse.ArgumentTypeError("--top must be an integer or 'all'") from exc
        if top <= 0:
            raise argparse.ArgumentTypeError("--top must be positive")
        return top

    if not candidates_file.exists():
        raise FileNotFoundError(
            f"Cannot resolve --top all because {candidates_file} does not exist. "
            "Run sync first or pass an explicit --top value."
        )
    payload = _read_json(candidates_file)
    return len(payload.get("candidates", []))


def build_convert_command(
    *,
    mode: str,
    top: int,
    timeout: int,
    lookback: str,
    report_path: Path,
    no_sync: bool,
    progress_interval: float | None = None,
    progress_every: int | None = None,
    profile: str = DEFAULT_PROFILE_NAME,
    discovery_report: Path | None = None,
    migration_plan_out: Path | None = None,
    workers: int = 1,
) -> list[str]:
    """Build the low-level converter command for a workflow mode."""
    command = [
        sys.executable,
        "scripts/convert_sentinel_kql.py",
        "--top",
        str(top),
        "--report",
        str(report_path),
        "--query-lookback",
        lookback,
        "--query-timeout",
        str(timeout),
        "--profile",
        profile,
    ]
    if discovery_report:
        command.extend(["--discovery-report", str(discovery_report)])
    if migration_plan_out:
        command.extend(["--migration-plan-out", str(migration_plan_out)])
    if no_sync:
        command.append("--no-sync")
    if progress_interval is not None:
        command.extend(["--progress-interval", str(progress_interval)])
    if progress_every is not None:
        command.extend(["--progress-every", str(progress_every)])
    if workers != 1:
        command.extend(["--workers", str(workers)])

    if mode == "local":
        command.append("--validate-local")
    elif mode == "promote":
        command.extend(["--validate-live", "--write-working", "--clean-output"])
    else:
        raise ValueError(f"unsupported converter mode: {mode}")
    return command


def run_command(command: list[str], dry_run: bool = False) -> None:
    """Run one workflow command, or print it in dry-run mode."""
    printable = " ".join(command)
    print(f"$ {printable}")
    if dry_run:
        return
    subprocess.run(command, cwd=PROJECT_DIR, check=True)


def load_report(report_path: Path = DEFAULT_REPORT_PATH) -> dict:
    """Load a Sentinel conversion report."""
    if not report_path.exists():
        raise FileNotFoundError(f"Sentinel conversion report not found: {report_path}")
    return _read_json(report_path)


def load_promoted_query_counts(sentinel_dir: Path = DEFAULT_SENTINEL_DIR) -> dict:
    """Return count breakdowns for promoted Sentinel query JSON files."""
    categories = Counter()
    levels = Counter()
    live_status = Counter()
    source_tables = Counter()
    files = sorted(sentinel_dir.glob("*.json")) if sentinel_dir.exists() else []
    for path in files:
        try:
            payload = _read_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        categories[payload.get("sentinel_category", "unknown")] += 1
        levels[payload.get("level", "unknown")] += 1
        live_status[payload.get("live_validation_status", "unknown")] += 1
        for table in payload.get("sentinel_tables", []):
            source_tables[table] += 1
    return {
        "files": len(files),
        "categories": dict(categories),
        "levels": dict(levels),
        "live_status": dict(live_status),
        "source_tables": dict(source_tables),
    }


def load_sentinel_dashboard_counts(inventory_path: Path = DEFAULT_DASHBOARD_INVENTORY) -> dict[str, int]:
    """Return Sentinel dashboard names and widget counts from dashboard inventory."""
    if not inventory_path.exists():
        return {}
    try:
        inventory = _read_json(inventory_path)
    except (OSError, json.JSONDecodeError):
        return {}
    dashboards = {}
    for dashboard in inventory.get("dashboards", []):
        name = dashboard.get("name", "")
        if name.startswith(SENTINEL_DASHBOARD_PREFIX):
            dashboards[name] = int(dashboard.get("widget_count", 0))
    return dict(sorted(dashboards.items()))


def build_status(
    *,
    report_path: Path = DEFAULT_REPORT_PATH,
    sentinel_dir: Path = DEFAULT_SENTINEL_DIR,
    dashboard_inventory: Path = DEFAULT_DASHBOARD_INVENTORY,
) -> dict:
    """Build a compact status summary across Sentinel report and artifacts."""
    report = load_report(report_path)
    summary = report.get("summary", {})
    runtime_profile = report.get("runtime_profile", {})
    promoted_counts = load_promoted_query_counts(sentinel_dir)
    dashboard_counts = load_sentinel_dashboard_counts(dashboard_inventory)
    promoted_files = promoted_counts.get("files", 0)
    live_status = promoted_counts.get("live_status", {})
    checks = {
        "promoted_count_matches_files": summary.get("promoted_count", 0) == promoted_files,
        "live_passed_matches_files": summary.get("live_validation_passed", 0) == promoted_files,
        "all_promoted_files_live_passed": set(live_status) <= {"passed"} and promoted_files > 0,
        "sentinel_dashboards_present": len(dashboard_counts) > 0,
    }
    return {
        "status": "ok" if all(checks.values()) else "attention",
        "summary": summary,
        "runtime_profile": runtime_profile,
        "promoted_files": promoted_files,
        "promoted_categories": promoted_counts.get("categories", {}),
        "promoted_live_status": live_status,
        "sentinel_dashboards": dashboard_counts,
        "checks": checks,
    }


def _top_items(counter_like: dict[str, int], limit: int = 12) -> list[tuple[str, int]]:
    return sorted(counter_like.items(), key=lambda item: (-item[1], item[0]))[:limit]


def _live_failures(report: dict, limit: int = 8) -> list[dict]:
    failures = [
        item for item in report.get("attempted", [])
        if item.get("live_validation_status") == "failed"
    ]
    return failures[:limit]


def _count_list_field(items: Iterable[dict], field_name: str) -> Counter:
    counter: Counter = Counter()
    for item in items:
        values = item.get(field_name, [])
        if isinstance(values, list):
            counter.update(str(value) for value in values if value)
        elif values:
            counter[str(values)] += 1
    return counter


def _as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item]
    if value:
        return [str(value)]
    return []


def _safe_error_summary(error: object, limit: int = 220) -> str:
    """Return a compact, redacted validation error for static docs."""
    parsed = error
    if isinstance(error, str):
        try:
            parsed = ast.literal_eval(error)
        except (SyntaxError, ValueError):
            parsed = error
    if isinstance(parsed, dict):
        status = parsed.get("status", "")
        code = parsed.get("code", "")
        message = parsed.get("message", "")
        text = f"status={status} code={code} message={message}".strip()
    else:
        text = str(parsed)
    text = re.sub(r"['\"]?opc-request-id['\"]?\s*:\s*['\"][^'\"]+['\"],?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def _first_reason_with_prefix(reasons: list[str], prefix: str) -> str:
    for reason in reasons:
        if reason.startswith(prefix):
            return reason
    return ""


def classify_next_query_candidate(item: dict) -> dict:
    """Classify a non-promoted Sentinel candidate into an actionable work type."""
    skip_reasons = _as_list(item.get("skip_reasons"))
    local_errors = _as_list(item.get("local_validation_errors"))
    live_status = item.get("live_validation_status", "")
    if live_status == "failed":
        reason = _safe_error_summary(item.get("live_validation_error", "")) or "live OCI validation failed"
        if "status=401" in reason or "code=NotAuthenticated" in reason or "clock skew" in reason:
            work_type = "live_environment"
        else:
            work_type = "live_validation"
    elif local_errors:
        work_type = "local_validation"
        reason = local_errors[0]
    elif field_reason := _first_reason_with_prefix(skip_reasons, "unsupported Sentinel field mapping:"):
        work_type = "field_mapping"
        reason = field_reason
    elif table_reason := _first_reason_with_prefix(skip_reasons, "unsupported Sentinel table:"):
        work_type = "table_mapping"
        reason = table_reason
    elif any(
        marker in reason
        for reason in skip_reasons
        for marker in (
            "unsupported KQL",
            "unsupported function",
            "unsupported aggregate",
            "JSON",
            "regex",
        )
    ):
        work_type = "kql_support"
        reason = skip_reasons[0] if skip_reasons else "unsupported KQL feature"
    else:
        work_type = "unsupported"
        reason = skip_reasons[0] if skip_reasons else "not promoted"

    return {
        "work_type": work_type,
        "reason": reason,
        "next_step": NEXT_QUERY_WORK_TYPES[work_type]["guidance"],
        "all_reasons": skip_reasons + local_errors,
    }


def _extract_mapping_blocker(reason: str, prefix: str) -> str:
    """Extract the missing Sentinel table or field from a skip reason."""
    if reason.startswith(prefix):
        return reason[len(prefix):].strip()
    return reason.strip()


def _build_oci_gap(work_type: str, reason: str) -> dict | None:
    """Build OCI parser/source follow-up details for mapping backlog entries."""
    if work_type == "field_mapping":
        blocked_on = _extract_mapping_blocker(reason, "unsupported Sentinel field mapping:")
    elif work_type == "table_mapping":
        blocked_on = _extract_mapping_blocker(reason, "unsupported Sentinel table:")
    else:
        return None
    return {
        "gap_type": work_type,
        "blocked_on": blocked_on,
        "oci_steps": list(OCI_GAP_STEPS),
    }


def build_next_query_backlog(
    report_path: Path = DEFAULT_REPORT_PATH,
    *,
    limit: int = 20,
    work_type: str = "all",
    strategy: str = "default",
) -> dict:
    """Build a prioritized backlog of specific Sentinel candidates to develop next."""
    report = load_report(report_path)
    requested_type = work_type.strip().lower()
    requested_strategy = strategy.strip().lower()
    if requested_strategy not in NEXT_QUERY_STRATEGIES:
        raise ValueError(f"unsupported next-query strategy: {strategy}")
    strategy_priority = {
        work_type_name: index
        for index, work_type_name in enumerate(NEXT_QUERY_STRATEGIES[requested_strategy])
    }
    candidates = []
    for item in report.get("attempted", []):
        if item.get("conversion_status") == "promoted" and item.get("live_validation_status") == "passed":
            continue
        classification = classify_next_query_candidate(item)
        if requested_type != "all" and classification["work_type"] != requested_type:
            continue
        candidate = {
            "title": item.get("title", ""),
            "sentinel_id": item.get("sentinel_id", ""),
            "quality_score": item.get("quality_score", 0),
            "source_path": item.get("source_path", ""),
            "source_url": item.get("source_url", ""),
            "work_type": classification["work_type"],
            "reason": classification["reason"],
            "next_step": classification["next_step"],
            "all_reasons": classification["all_reasons"],
            "_priority": strategy_priority[classification["work_type"]],
        }
        oci_gap = _build_oci_gap(classification["work_type"], classification["reason"])
        if oci_gap:
            candidate["oci_gap"] = oci_gap
        candidates.append(candidate)
    candidates.sort(key=lambda item: (
        item["_priority"],
        -int(item.get("quality_score", 0)),
        item.get("title", ""),
        item.get("source_path", ""),
    ))
    for candidate in candidates:
        candidate.pop("_priority", None)
    return {
        "summary": report.get("summary", {}),
        "work_type": requested_type,
        "strategy": requested_strategy,
        "candidates": candidates[:limit],
        "candidate_count": len(candidates),
        "work_type_counts": dict(Counter(candidate["work_type"] for candidate in candidates)),
    }


def _count_rows(counter_like: dict[str, int], limit: int) -> list[dict]:
    return [
        {"reason": reason, "count": count}
        for reason, count in _top_items(counter_like, limit=limit)
    ]


def _build_next_actions(skip_reasons: Counter, local_errors: Counter, live_failures: list[dict]) -> list[str]:
    actions = []
    field_mapping_count = sum(
        count for reason, count in skip_reasons.items()
        if reason.startswith("unsupported Sentinel field mapping:")
    )
    table_mapping_count = sum(
        count for reason, count in skip_reasons.items()
        if reason.startswith("unsupported Sentinel table:")
    )
    if field_mapping_count:
        actions.append(
            f"Review {field_mapping_count} unsupported field-mapping skips against "
            "queries/log_source_field_dictionary.json before extending config/sentinel_oci_mapping.yaml."
        )
    if table_mapping_count:
        actions.append(
            f"Review {table_mapping_count} unsupported table skips and add source mappings only when "
            "there is a real OCI Log Analytics source/parser target."
        )
    if local_errors:
        actions.append("Fix local validation errors before attempting live promotion for those candidates.")
    if live_failures:
        actions.append(
            "Inspect live validation failures for Logan syntax or parser-field mismatches; they are kept "
            "out of queries/sentinel/ until they pass live validation."
        )
    if not actions:
        actions.append("No conversion blockers found in the current report.")
    return actions


def build_triage(report_path: Path = DEFAULT_REPORT_PATH, limit: int = 10) -> dict:
    """Build a report-first triage summary for skipped and live-failed Sentinel candidates."""
    report = load_report(report_path)
    attempted = report.get("attempted", [])
    skip_reasons = _count_list_field(attempted, "skip_reasons")
    local_errors = _count_list_field(attempted, "local_validation_errors")
    live_failures = _live_failures(report, limit=limit)
    failure_examples = [
        {
            "title": failure.get("title", ""),
            "source_path": failure.get("source_path", ""),
            "error": _safe_error_summary(failure.get("live_validation_error", "")),
        }
        for failure in live_failures
    ]
    unsupported = report.get("unsupported_features", {})
    return {
        "summary": report.get("summary", {}),
        "top_skip_reasons": _count_rows(skip_reasons, limit),
        "top_local_validation_errors": _count_rows(local_errors, limit),
        "top_unsupported_features": _count_rows(unsupported, limit),
        "live_failure_examples": failure_examples,
        "next_actions": _build_next_actions(skip_reasons, local_errors, live_failures),
    }


def _html_table(headers: Iterable[str], rows: Iterable[Iterable[object]], empty: str) -> str:
    headers = list(headers)
    rows = list(rows)
    header_html = "".join(f"<th>{html.escape(str(header))}</th>" for header in headers)
    if not rows:
        column_count = len(headers)
        return (
            "<table>"
            f"<thead><tr>{header_html}</tr></thead>"
            f"<tbody><tr><td colspan=\"{column_count}\">{html.escape(empty)}</td></tr></tbody>"
            "</table>"
        )
    body = []
    for row in rows:
        body.append("<tr>" + "".join(f"<td>{html.escape(str(cell))}</td>" for cell in row) + "</tr>")
    return f"<table><thead><tr>{header_html}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def render_report_html(
    report: dict,
    *,
    sentinel_counts: dict | None = None,
    dashboard_counts: dict[str, int] | None = None,
    generated_at: datetime | None = None,
) -> str:
    """Render a static HTML review page for the Sentinel conversion report."""
    sentinel_counts = sentinel_counts or {}
    dashboard_counts = dashboard_counts or {}
    generated_at = generated_at or datetime.now(timezone.utc)
    summary = report.get("summary", {})
    source = report.get("source", {})
    unsupported = report.get("unsupported_features", {})
    categories = sentinel_counts.get("categories", {})
    levels = sentinel_counts.get("levels", {})
    live_status = sentinel_counts.get("live_status", {})

    metrics = [
        ("Candidates", summary.get("total_candidates", 0)),
        ("Attempted", summary.get("attempted_candidates", 0)),
        ("Promoted", summary.get("promoted_count", 0)),
        ("Live passed", summary.get("live_validation_passed", 0)),
        ("Live failed", summary.get("live_validation_failed", 0)),
        ("Promoted files", sentinel_counts.get("files", 0)),
    ]
    metric_html = "".join(
        "<section class=\"metric\">"
        f"<span>{html.escape(label)}</span>"
        f"<strong>{html.escape(str(value))}</strong>"
        "</section>"
        for label, value in metrics
    )

    category_rows = _top_items(categories)
    max_category = max((count for _name, count in category_rows), default=1)
    category_html = "".join(
        "<div class=\"bar-row\">"
        f"<span>{html.escape(name)}</span>"
        "<div class=\"bar-track\">"
        f"<div class=\"bar\" style=\"width: {int((count / max_category) * 100)}%\"></div>"
        "</div>"
        f"<strong>{count}</strong>"
        "</div>"
        for name, count in category_rows
    ) or "<p class=\"muted\">No promoted Sentinel queries found.</p>"

    dashboard_table = _html_table(
        ["Dashboard", "Widgets"],
        dashboard_counts.items(),
        "Dashboard inventory has not been generated.",
    )
    unsupported_table = _html_table(
        ["Reason", "Count"],
        _top_items(unsupported, limit=16),
        "No unsupported features recorded.",
    )
    failures_table = _html_table(
        ["Title", "Source path", "Error"],
        (
            (
                failure.get("title", ""),
                failure.get("source_path", ""),
                _safe_error_summary(failure.get("live_validation_error", "")),
            )
            for failure in _live_failures(report)
        ),
        "No live validation failures in the report.",
    )
    levels_table = _html_table(["Severity", "Promoted"], _top_items(levels), "No promoted severities.")
    live_table = _html_table(["Live status", "Promoted files"], _top_items(live_status), "No promoted live status.")

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Sentinel to Logan QL Conversion</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #17202a;
      --muted: #5f6b7a;
      --line: #d9e0e8;
      --panel: #f7f9fb;
      --accent: #0f766e;
      --accent-2: #b45309;
      --accent-3: #1d4ed8;
      --white: #ffffff;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background: var(--white);
      font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    header {{
      padding: 32px clamp(20px, 5vw, 64px) 24px;
      border-bottom: 1px solid var(--line);
      background: linear-gradient(90deg, #f8fafc, #f1f8f6 45%, #fff7ed);
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: clamp(28px, 4vw, 44px);
      line-height: 1.1;
      letter-spacing: 0;
    }}
    h2 {{
      margin: 0 0 14px;
      font-size: 20px;
      letter-spacing: 0;
    }}
    main {{
      padding: 28px clamp(20px, 5vw, 64px) 48px;
    }}
    .lede {{
      max-width: 980px;
      margin: 0;
      color: var(--muted);
      font-size: 16px;
    }}
    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px 24px;
      margin-top: 18px;
      color: var(--muted);
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(145px, 1fr));
      gap: 12px;
      margin: 0 0 28px;
    }}
    .metric {{
      min-height: 96px;
      padding: 16px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
    }}
    .metric span {{
      display: block;
      color: var(--muted);
      font-size: 13px;
    }}
    .metric strong {{
      display: block;
      margin-top: 8px;
      font-size: 30px;
      line-height: 1;
    }}
    .grid {{
      display: grid;
      grid-template-columns: minmax(0, 1.15fr) minmax(280px, 0.85fr);
      gap: 18px;
      align-items: start;
    }}
    section.panel {{
      margin-bottom: 18px;
      padding: 18px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--white);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    th, td {{
      padding: 10px 9px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
    }}
    th {{
      color: var(--muted);
      font-weight: 650;
      background: #f8fafc;
    }}
    .bar-row {{
      display: grid;
      grid-template-columns: minmax(105px, 170px) 1fr 48px;
      gap: 12px;
      align-items: center;
      margin: 10px 0;
    }}
    .bar-track {{
      height: 14px;
      border-radius: 999px;
      background: #edf2f7;
      overflow: hidden;
    }}
    .bar {{
      height: 100%;
      border-radius: 999px;
      background: linear-gradient(90deg, var(--accent), var(--accent-3));
    }}
    code {{
      padding: 2px 5px;
      border-radius: 5px;
      background: #eef2ff;
      color: #1e3a8a;
    }}
    pre {{
      overflow-x: auto;
      padding: 14px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #111827;
      color: #f9fafb;
    }}
    .muted {{ color: var(--muted); }}
    .callout {{
      border-left: 4px solid var(--accent-2);
      padding-left: 14px;
      color: var(--muted);
    }}
    @media (max-width: 820px) {{
      .grid {{ grid-template-columns: 1fr; }}
      .bar-row {{ grid-template-columns: 1fr; gap: 6px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Sentinel to Logan QL Conversion</h1>
    <p class="lede">Static review page for the Microsoft Sentinel conversion pipeline. Promoted queries are source-attributed, mapped to real OCI Log Analytics fields, and written only after live parser validation.</p>
    <div class="meta">
      <span>Generated: {html.escape(generated_at.isoformat())}</span>
      <span>Source: {html.escape(str(source.get("repository", "Microsoft Sentinel")))}</span>
      <span>Ranking: {html.escape(str(summary.get("ranking", "quality-first")))}</span>
    </div>
  </header>
  <main>
    <div class="metrics">{metric_html}</div>
    <div class="grid">
      <div>
        <section class="panel">
          <h2>Promoted Categories</h2>
          {category_html}
        </section>
        <section class="panel">
          <h2>Sentinel Dashboards</h2>
          {dashboard_table}
        </section>
        <section class="panel">
          <h2>Top Skip Reasons</h2>
          {unsupported_table}
        </section>
        <section class="panel">
          <h2>Live Validation Failures Kept Out</h2>
          {failures_table}
        </section>
      </div>
      <aside>
        <section class="panel">
          <h2>Severity Mix</h2>
          {levels_table}
        </section>
        <section class="panel">
          <h2>Promoted Live Status</h2>
          {live_table}
        </section>
        <section class="panel">
          <h2>Operator Commands</h2>
          <pre>python3 scripts/sentinel_conversion_workflow.py local
python3 scripts/sentinel_conversion_workflow.py promote --top all --timeout 20
python3 scripts/sentinel_conversion_workflow.py promote --top all --timeout 60 --progress-interval 0
python3 scripts/sentinel_conversion_workflow.py refresh-artifacts
python3 scripts/sentinel_conversion_workflow.py triage
python3 scripts/sentinel_conversion_workflow.py next-queries --limit 10
python3 scripts/sentinel_conversion_workflow.py next-queries --strategy foundational --limit 10
python3 scripts/sentinel_conversion_workflow.py status --json --strict</pre>
          <p class="callout">The local command writes to <code>/tmp/sentinel_conversion_local.json</code> by default so it does not overwrite the canonical live validation report.</p>
        </section>
      </aside>
    </div>
  </main>
</body>
</html>
"""


def write_report_html(
    *,
    report_path: Path = DEFAULT_REPORT_PATH,
    output_path: Path = DEFAULT_HTML_PATH,
    sentinel_dir: Path = DEFAULT_SENTINEL_DIR,
    dashboard_inventory: Path = DEFAULT_DASHBOARD_INVENTORY,
) -> Path:
    """Write the static HTML report page and return its path."""
    report = load_report(report_path)
    html_text = render_report_html(
        report,
        sentinel_counts=load_promoted_query_counts(sentinel_dir),
        dashboard_counts=load_sentinel_dashboard_counts(dashboard_inventory),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_text, encoding="utf-8")
    return output_path


def _print_report_summary(report_path: Path, sentinel_dir: Path = DEFAULT_SENTINEL_DIR) -> None:
    report = load_report(report_path)
    summary = report.get("summary", {})
    promoted_files = len(list(sentinel_dir.glob("*.json"))) if sentinel_dir.exists() else 0
    print(
        "Sentinel conversion summary: "
        f"promoted={summary.get('promoted_count', 0)}, "
        f"live_passed={summary.get('live_validation_passed', 0)}, "
        f"live_failed={summary.get('live_validation_failed', 0)}, "
        f"files={promoted_files}"
    )


def print_status(status: dict, as_json: bool = False) -> None:
    """Print Sentinel workflow status in human or JSON form."""
    if as_json:
        print(json.dumps(status, indent=2, sort_keys=True))
        return

    summary = status.get("summary", {})
    print(f"Sentinel workflow status: {status.get('status', 'unknown')}")
    print(f"  promoted_count: {summary.get('promoted_count', 0)}")
    print(f"  promoted_files: {status.get('promoted_files', 0)}")
    print(f"  live_passed:    {summary.get('live_validation_passed', 0)}")
    print(f"  live_failed:    {summary.get('live_validation_failed', 0)}")
    profile = status.get("runtime_profile", {})
    if profile:
        print(f"  profile:        {profile.get('name', 'unknown')}")
    print("  checks:")
    for name, ok in status.get("checks", {}).items():
        print(f"    {'OK' if ok else 'ATTN'} {name}")
    dashboards = status.get("sentinel_dashboards", {})
    if dashboards:
        print("  dashboards:")
        for name, count in dashboards.items():
            print(f"    {count:>2} {name}")


def _print_reason_rows(rows: list[dict], empty: str) -> None:
    if not rows:
        print(f"    {empty}")
        return
    for row in rows:
        print(f"    {row.get('count', 0):>4} {row.get('reason', '')}")


def print_triage(triage: dict, as_json: bool = False) -> None:
    """Print Sentinel conversion triage in human or JSON form."""
    if as_json:
        print(json.dumps(triage, indent=2, sort_keys=True))
        return

    summary = triage.get("summary", {})
    print("Sentinel conversion triage")
    print(f"  attempted:     {summary.get('attempted_candidates', 0)}")
    print(f"  promoted:      {summary.get('promoted_count', 0)}")
    print(f"  skipped:       {summary.get('skipped_count', 0)}")
    print(f"  live_failed:   {summary.get('live_validation_failed', 0)}")
    print("  top skip reasons:")
    _print_reason_rows(triage.get("top_skip_reasons", []), "No skip reasons found.")
    print("  top local validation errors:")
    _print_reason_rows(triage.get("top_local_validation_errors", []), "No local validation errors found.")
    failures = triage.get("live_failure_examples", [])
    print("  live failure examples:")
    if not failures:
        print("    No live validation failures found.")
    for failure in failures:
        print(f"    - {failure.get('title', '')} [{failure.get('source_path', '')}]")
        print(f"      {failure.get('error', '')}")
    print("  next actions:")
    for action in triage.get("next_actions", []):
        print(f"    - {action}")


def print_next_query_backlog(backlog: dict, as_json: bool = False) -> None:
    """Print next-query backlog in human or JSON form."""
    if as_json:
        print(json.dumps(backlog, indent=2, sort_keys=True))
        return

    print("Sentinel next-query backlog")
    print(f"  work_type:       {backlog.get('work_type', 'all')}")
    print(f"  strategy:        {backlog.get('strategy', 'default')}")
    print(f"  matching_items:  {backlog.get('candidate_count', 0)}")
    counts = backlog.get("work_type_counts", {})
    if counts:
        print("  work_type_counts:")
        strategy = backlog.get("strategy", "default")
        strategy_priority = {
            work_type_name: index
            for index, work_type_name in enumerate(NEXT_QUERY_STRATEGIES.get(strategy, NEXT_QUERY_STRATEGIES["default"]))
        }
        for name, count in sorted(counts.items(), key=lambda item: (strategy_priority[item[0]], item[0])):
            print(f"    {count:>4} {name}")
    print("  candidates:")
    candidates = backlog.get("candidates", [])
    if not candidates:
        print("    No matching candidates.")
        return
    for candidate in candidates:
        print(
            f"    - [{candidate.get('work_type', '')}] "
            f"score={candidate.get('quality_score', 0)} {candidate.get('title', '')}"
        )
        print(f"      source: {candidate.get('source_path', '')}")
        print(f"      reason: {candidate.get('reason', '')}")
        print(f"      next: {candidate.get('next_step', '')}")
        if oci_gap := candidate.get("oci_gap"):
            print(f"      oci_gap: {oci_gap.get('gap_type', '')} blocked_on={oci_gap.get('blocked_on', '')}")


def run_convert_mode(args, mode: str, report_path: Path) -> None:
    top = resolve_top(args.top, Path(args.candidates_file))
    command = build_convert_command(
        mode=mode,
        top=top,
        timeout=args.timeout,
        lookback=args.lookback,
        report_path=report_path,
        no_sync=args.no_sync,
        progress_interval=args.progress_interval,
        progress_every=args.progress_every,
        profile=args.profile,
        discovery_report=Path(args.discovery_report) if args.discovery_report else None,
        migration_plan_out=Path(args.migration_plan_out) if args.migration_plan_out else None,
        workers=args.workers,
    )
    if args.candidates_file != str(DEFAULT_CANDIDATES_FILE):
        command.extend(["--candidates-file", args.candidates_file])
    run_command(command, dry_run=args.dry_run)
    if not args.dry_run:
        _print_report_summary(report_path)


def refresh_artifacts(args) -> None:
    commands = [
        [sys.executable, "scripts/generate_catalog.py"],
        [sys.executable, "scripts/deploy_dashboard.py", "--export-inventory"],
        [sys.executable, "scripts/deploy_dashboard.py", "--validate"],
    ]
    for command in commands:
        run_command(command, dry_run=args.dry_run)


def run_synthetic_plan(args) -> None:
    """Build parser-aware synthetic logs for a Sentinel candidate batch."""
    top = resolve_top(args.top, Path(args.candidates_file))
    command = [
        sys.executable,
        "scripts/sentinel_synthetic_logs.py",
        "plan",
        "--top",
        str(top),
        "--candidates-file",
        args.candidates_file,
        "--data-dir",
        args.synthetic_data_dir,
        "--out",
        args.synthetic_plan,
        "--progress-interval",
        str(args.progress_interval),
        "--progress-every",
        str(args.progress_every),
    ]
    run_command(command, dry_run=args.dry_run)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Microsoft Sentinel to Logan QL conversion workflow."
    )
    parser.add_argument(
        "command",
        choices=[
            "local",
            "promote",
            "refresh-artifacts",
            "page",
            "status",
            "triage",
            "next-queries",
            "synthetic-plan",
            "all",
        ],
        help="Workflow step to run.",
    )
    parser.add_argument("--top", default="all", help="Candidates to attempt: integer or 'all'.")
    parser.add_argument("--timeout", type=int, default=20, help="Per-query live validation timeout.")
    parser.add_argument("--lookback", default="24h", help="Live validation query lookback.")
    parser.add_argument("--no-sync", action="store_true", default=True, help="Use cached Sentinel intake.")
    parser.add_argument("--sync", dest="no_sync", action="store_false", help="Allow converter sync if needed.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    parser.add_argument(
        "--progress-interval",
        type=float,
        default=30.0,
        help="Seconds between converter progress lines; set 0 for every candidate, -1 to disable.",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=100,
        help="Emit converter candidate progress at least every N attempted candidates.",
    )
    parser.add_argument("--candidates-file", default=str(DEFAULT_CANDIDATES_FILE))
    parser.add_argument("--local-report", default=str(DEFAULT_LOCAL_REPORT_PATH))
    parser.add_argument("--report", default=str(DEFAULT_REPORT_PATH))
    parser.add_argument("--profile", default=DEFAULT_PROFILE_NAME, help="Runtime mapping profile name or YAML path.")
    parser.add_argument("--discovery-report", default="", help="Optional SIEM discovery inventory/report for ranking.")
    parser.add_argument("--migration-plan-out", default="", help="Optional migration plan JSON output.")
    parser.add_argument("--html", default=str(DEFAULT_HTML_PATH))
    parser.add_argument("--sentinel-dir", default=str(DEFAULT_SENTINEL_DIR))
    parser.add_argument("--dashboard-inventory", default=str(DEFAULT_DASHBOARD_INVENTORY))
    parser.add_argument("--synthetic-plan", default=str(PROJECT_DIR / "queries" / "sentinel_synthetic_plan.json"))
    parser.add_argument("--synthetic-data-dir", default=str(PROJECT_DIR / "test_data" / "sentinel_synthetic"))
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON for status, triage, or next-queries.")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when status checks need attention.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum rows for triage or next-queries sections.")
    parser.add_argument(
        "--work-type",
        choices=["all", *NEXT_QUERY_WORK_TYPES.keys()],
        default="all",
        help="Filter next-queries output by work type.",
    )
    parser.add_argument(
        "--strategy",
        choices=sorted(NEXT_QUERY_STRATEGIES.keys()),
        default="default",
        help="Prioritization strategy for next-queries output.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=min(8, os.cpu_count() or 1),
        help=(
            "Parallel conversion worker threads for the CPU-bound convert_candidate phase "
            "(local and promote commands only). 1 = serial. Default: min(8, cpu_count)."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report_path = Path(args.report)
    local_report_path = Path(args.local_report)
    html_path = Path(args.html)
    sentinel_dir = Path(args.sentinel_dir)
    dashboard_inventory = Path(args.dashboard_inventory)
    bind(
        log,
        command=args.command,
        dry_run=getattr(args, "dry_run", False),
        workers=getattr(args, "workers", 1),
    ).info("sentinel_workflow.start")

    if args.command == "local":
        run_convert_mode(args, "local", local_report_path)
        if not args.dry_run:
            print(f"Local report: {_project_relative(local_report_path)}")
        return 0

    if args.command == "promote":
        run_convert_mode(args, "promote", report_path)
        if not args.dry_run:
            output_path = write_report_html(
                report_path=report_path,
                output_path=html_path,
                sentinel_dir=sentinel_dir,
                dashboard_inventory=dashboard_inventory,
            )
            print(f"HTML report: {_project_relative(output_path)}")
        return 0

    if args.command == "refresh-artifacts":
        refresh_artifacts(args)
        if not args.dry_run:
            output_path = write_report_html(
                report_path=report_path,
                output_path=html_path,
                sentinel_dir=sentinel_dir,
                dashboard_inventory=dashboard_inventory,
            )
            print(f"HTML report: {_project_relative(output_path)}")
        return 0

    if args.command == "page":
        if not args.dry_run:
            output_path = write_report_html(
                report_path=report_path,
                output_path=html_path,
                sentinel_dir=sentinel_dir,
                dashboard_inventory=dashboard_inventory,
            )
            print(f"HTML report: {_project_relative(output_path)}")
        else:
            print(f"Would render HTML report to {_project_relative(html_path)}")
        return 0

    if args.command == "status":
        if args.dry_run:
            print("Would load Sentinel report, promoted query files, and dashboard inventory.")
        else:
            status = build_status(
                report_path=report_path,
                sentinel_dir=sentinel_dir,
                dashboard_inventory=dashboard_inventory,
            )
            print_status(status, as_json=args.json)
            if args.strict and status.get("status") != "ok":
                return 1
        return 0

    if args.command == "triage":
        if args.dry_run:
            print("Would load Sentinel report and summarize skip, local-validation, and live-failure blockers.")
        else:
            print_triage(build_triage(report_path=report_path, limit=args.limit), as_json=args.json)
        return 0

    if args.command == "next-queries":
        if args.dry_run:
            print("Would load Sentinel report and build a prioritized next-query development backlog.")
        else:
            print_next_query_backlog(
                build_next_query_backlog(
                    report_path=report_path,
                    limit=args.limit,
                    work_type=args.work_type,
                    strategy=args.strategy,
                ),
                as_json=args.json,
            )
        return 0

    if args.command == "synthetic-plan":
        run_synthetic_plan(args)
        return 0

    if args.command == "all":
        run_convert_mode(args, "promote", report_path)
        refresh_artifacts(args)
        if not args.dry_run:
            output_path = write_report_html(
                report_path=report_path,
                output_path=html_path,
                sentinel_dir=sentinel_dir,
                dashboard_inventory=dashboard_inventory,
            )
            print(f"HTML report: {_project_relative(output_path)}")
        return 0

    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
