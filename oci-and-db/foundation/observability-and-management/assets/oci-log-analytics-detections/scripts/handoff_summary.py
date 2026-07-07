#!/usr/bin/env python3
"""Build a concise handoff summary from release evidence and GSD state."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parent.parent
HEALTH_DIR = PROJECT_DIR / "docs" / "health"

OCID_RE = re.compile(r"\bocid1\.[A-Za-z0-9][A-Za-z0-9._-]{8,}\b", re.IGNORECASE)
REQUEST_ID_RE = re.compile(r"(?i)(opc[-_]request[-_]id\s*[:=]\s*)[A-Za-z0-9._:-]{12,}")
PRIVATE_KEY_RE = re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")


class HandoffError(RuntimeError):
    """Raised when handoff summary generation is unsafe or impossible."""


def _project_relative(path: Path, project_dir: Path) -> str:
    try:
        return str(path.resolve().relative_to(project_dir.resolve()))
    except ValueError:
        return str(path)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise HandoffError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise HandoffError(f"invalid JSON in {path}: {exc}") from exc


def _redact_text(value: str) -> str:
    value = OCID_RE.sub("<redacted:ocid>", value)
    value = REQUEST_ID_RE.sub(r"\1<redacted:opc_request_id>", value)
    value = PRIVATE_KEY_RE.sub("<redacted:private_key>", value)
    return value


def _sanitize(value: Any) -> Any:
    if isinstance(value, str):
        return _redact_text(value)
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if isinstance(value, dict):
        return {key: _sanitize(item) for key, item in value.items()}
    return value


def _parse_generated_at(path: Path) -> str:
    try:
        return str(_load_json(path).get("generated_at", ""))
    except HandoffError:
        return ""


def discover_latest_release_report(health_dir: Path = HEALTH_DIR) -> Path:
    candidates = [
        path
        for path in health_dir.glob("release-checklist*.json")
        if path.is_file()
    ]
    if not candidates:
        raise HandoffError(f"no release checklist reports found under {health_dir}")
    return max(candidates, key=lambda path: (_parse_generated_at(path), path.stat().st_mtime, path.name))


def _extract_line_value(text: str, label: str) -> str:
    pattern = re.compile(rf"^{re.escape(label)}:\s*(.+?)\s*$", re.MULTILINE)
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def _parse_state(project_dir: Path) -> dict[str, Any]:
    path = project_dir / ".planning" / "STATE.md"
    if not path.exists():
        return {"exists": False}
    text = path.read_text(encoding="utf-8")
    return {
        "exists": True,
        "path": _project_relative(path, project_dir),
        "phase": _extract_line_value(text, "Phase"),
        "plan": _extract_line_value(text, "Plan"),
        "status": _extract_line_value(text, "Status"),
        "last_activity": _extract_line_value(text, "Last activity"),
        "progress": _extract_line_value(text, "Progress"),
    }


def _parse_roadmap(project_dir: Path) -> dict[str, Any]:
    path = project_dir / ".planning" / "ROADMAP.md"
    if not path.exists():
        return {"exists": False}
    text = path.read_text(encoding="utf-8")
    phase_lines = re.findall(r"^- \[[ x]\] \*\*Phase \d+:", text, flags=re.MULTILINE)
    completed_phase_lines = re.findall(r"^- \[x\] \*\*Phase \d+:", text, flags=re.MULTILINE)
    phase_five_plan_lines = re.findall(r"^- \[[ x]\] 05-\d+:", text, flags=re.MULTILINE)
    phase_five_completed = re.findall(r"^- \[x\] 05-\d+:", text, flags=re.MULTILINE)
    return {
        "exists": True,
        "path": _project_relative(path, project_dir),
        "completed_phases": len(completed_phase_lines),
        "total_phases": len(phase_lines),
        "phase_5_completed_plans": len(phase_five_completed),
        "phase_5_total_plans": len(phase_five_plan_lines),
    }


def _artifact_counts(project_dir: Path) -> dict[str, Any]:
    queries = project_dir / "queries"
    artifacts: dict[str, Any] = {}

    catalog = _load_json(queries / "catalog.json")
    catalog_inventory = catalog.get("inventory", {})
    artifacts["catalog"] = {
        "total_rules": catalog.get("total_rules", 0),
        "total_content_items": catalog.get("total_content_items", catalog_inventory.get("total_query_artifacts", 0)),
        "source_yaml_rules": catalog_inventory.get("source_yaml_rules", 0),
        "total_query_artifacts": catalog_inventory.get("total_query_artifacts", 0),
        "generated_sentinel_queries": catalog_inventory.get("generated_sentinel_queries", 0),
    }

    dashboard = _load_json(queries / "dashboard_inventory.json")
    dashboard_summary = dashboard.get("summary", {})
    artifacts["dashboard_inventory"] = {
        "total_dashboards": dashboard_summary.get("total_dashboards", 0),
        "total_widgets": dashboard_summary.get("total_widgets", 0),
        "advanced_visualization_widgets": dashboard_summary.get("advanced_visualization_widgets", 0),
    }

    sentinel = _load_json(queries / "sentinel_conversion_report.json")
    sentinel_summary = sentinel.get("summary", {})
    artifacts["sentinel_conversion_report"] = {
        "promoted_count": sentinel_summary.get("promoted_count", 0),
        "live_validation_passed": sentinel_summary.get("live_validation_passed", 0),
        "live_validation_failed": sentinel_summary.get("live_validation_failed", 0),
    }

    dictionary = _load_json(queries / "log_source_field_dictionary.json")
    dictionary_summary = dictionary.get("summary", {})
    artifacts["field_dictionary"] = {
        "total_fields": dictionary_summary.get("total_fields", 0),
        "parser_count": dictionary_summary.get("parser_count", 0),
        "source_count": dictionary_summary.get("source_count", 0),
    }

    octo = _load_json(queries / "octo_apm_workshop_bundle.json")
    artifacts["octo_apm_workshop_bundle"] = {
        "dashboard_widgets": octo.get("dashboard", {}).get("widget_count", 0),
        "queries": len(octo.get("queries", [])),
        "detection_rule_specs": octo.get("detection_rules", {}).get("spec_count", 0),
        "deployable_detection_rules": octo.get("detection_rules", {}).get("deployable_count", 0),
    }

    return artifacts


def _release_summary(report_path: Path, report: dict[str, Any], project_dir: Path) -> dict[str, Any]:
    steps = report.get("steps", [])
    failed_steps = [
        {"name": step.get("name", ""), "exit_code": step.get("exit_code")}
        for step in steps
        if not step.get("ok", False)
    ]
    local_steps = [
        step for step in steps
        if step.get("name") != "live profile dashboard verification"
    ]
    return {
        "report_path": _project_relative(report_path, project_dir),
        "generated_at": report.get("generated_at", ""),
        "include_live": bool(report.get("include_live", False)),
        "overall_status": report.get("overall_status", ""),
        "step_count": len(steps),
        "local_step_count": len(local_steps),
        "failed_steps": failed_steps,
        "step_statuses": [
            {
                "name": step.get("name", ""),
                "ok": bool(step.get("ok", False)),
                "exit_code": step.get("exit_code"),
            }
            for step in steps
        ],
    }


def _next_command(include_live: bool) -> str:
    if include_live:
        return "$gsd-progress"
    return "python3 scripts/release_checklist.py --include-live --report docs/health/release-checklist-live.json"


def build_summary(release_report: Path | None = None, *, project_dir: Path = PROJECT_DIR) -> dict[str, Any]:
    project_dir = project_dir.resolve()
    report_path = release_report.resolve() if release_report else discover_latest_release_report(project_dir / "docs" / "health")
    if not report_path.exists():
        raise HandoffError(f"release report not found: {report_path}")

    report = _load_json(report_path)
    if report.get("overall_status") != "PASS":
        raise HandoffError(f"release report did not pass: {report_path}")

    summary = {
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "release": _release_summary(report_path, report, project_dir),
        "gsd_state": _parse_state(project_dir),
        "roadmap": _parse_roadmap(project_dir),
        "artifacts": _artifact_counts(project_dir),
        "next_command": _next_command(bool(report.get("include_live", False))),
    }
    return _sanitize(summary)


def write_summary(
    release_report: Path | None = None,
    *,
    out: Path = HEALTH_DIR / "latest-handoff.json",
    project_dir: Path = PROJECT_DIR,
) -> dict[str, Any]:
    summary = build_summary(release_report, project_dir=project_dir)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write a safe release handoff summary")
    parser.add_argument("--release-report", help="Release checklist report to summarize")
    parser.add_argument("--latest", action="store_true", help="Use the latest release-checklist report under docs/health")
    parser.add_argument("--out", default=str(HEALTH_DIR / "latest-handoff.json"), help="Output handoff JSON path")
    parser.add_argument("--project-dir", default=str(PROJECT_DIR), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    project_dir = Path(args.project_dir).resolve()
    release_report = Path(args.release_report) if args.release_report else None
    try:
        summary = write_summary(
            release_report,
            out=Path(args.out),
            project_dir=project_dir,
        )
    except HandoffError as exc:
        print(f"handoff summary failed: {exc}", file=sys.stderr)
        return 1
    print(f"Handoff summary: {args.out}")
    print(f"Next command: {summary['next_command']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
