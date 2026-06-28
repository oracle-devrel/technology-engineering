#!/usr/bin/env python3
"""Run the local release checklist for the OCI Log Analytics detection engine.

The default mode performs only local/offline or dry-run gates. Live
``<OCI_PROFILE>`` checks are explicit via ``--include-live`` and do not mutate
OCI resources.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_DIR / "scripts"
HEALTH_DIR = PROJECT_DIR / "docs" / "health"
SENTINEL_BACKLOG_PRIORITY_PATH = PROJECT_DIR / "queries" / "sentinel_backlog_priority.json"

OCID_RE = re.compile(r"\bocid1\.[A-Za-z0-9][A-Za-z0-9._-]{8,}\b", re.IGNORECASE)
REQUEST_ID_RE = re.compile(r"(?i)(opc[-_]request[-_]id\s*[:=]\s*)[A-Za-z0-9._:-]{12,}")
PRIVATE_KEY_RE = re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")
IPV4_RE = re.compile(
    r"(?<![\d.])"
    r"(?:25[0-5]|2[0-4]\d|1?\d?\d)"
    r"(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}"
    r"(?![\d.])"
)


def _redact_ipv4(match: re.Match[str]) -> str:
    value = match.group(0)
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return value
    return "<redacted:public_ip>" if ip.is_global else value


def _redact_output(output: str) -> str:
    output = OCID_RE.sub("<redacted:ocid>", output)
    output = REQUEST_ID_RE.sub(r"\1<redacted:opc_request_id>", output)
    output = PRIVATE_KEY_RE.sub("<redacted:private_key>", output)
    output = IPV4_RE.sub(_redact_ipv4, output)
    return output


def _run_step(name: str, command: list[str], timeout: int = 2400) -> dict:
    started = datetime.now(timezone.utc).isoformat()
    try:
        result = subprocess.run(
            command,
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        output = _redact_output(result.stdout + result.stderr)
        return {
            "name": name,
            "command": command,
            "started_at": started,
            "exit_code": result.returncode,
            "ok": result.returncode == 0,
            "output_tail": output[-6000:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "name": name,
            "command": command,
            "started_at": started,
            "exit_code": 124,
            "ok": False,
            "output_tail": _redact_output(f"TIMEOUT after {timeout}s: {exc}"),
        }


def build_steps(include_live: bool, skip_tests: bool, lookback: str, query_timeout: int) -> list[tuple[str, list[str], int]]:
    python = sys.executable
    steps: list[tuple[str, list[str], int]] = [
        ("log source dry run", [python, str(SCRIPTS_DIR / "setup_log_sources.py"), "--dry-run"], 300),
        ("synthetic log contract validation", [python, str(SCRIPTS_DIR / "validate_synthetic_logs.py")], 300),
        ("threat-intel candidate inventory", [python, str(SCRIPTS_DIR / "content_discovery.py")], 300),
        ("field dictionary validation", [python, str(SCRIPTS_DIR / "field_dictionary.py"), "--validate-query-fields"], 300),
        ("siem discovery schema validation", [python, str(SCRIPTS_DIR / "siem_discovery_report.py"), "sentinel"], 300),
        (
            "migration plan/report validation",
            [
                python,
                str(SCRIPTS_DIR / "siem_discovery_report.py"),
                "report",
                "--report-only",
            ],
            300,
        ),
        ("sentinel feed dependency bundle", [python, str(SCRIPTS_DIR / "sentinel_feed_dependencies.py")], 300),
        ("detection rule spec export", [python, str(SCRIPTS_DIR / "detection_rule_creator.py"), "--write-default"], 300),
        ("osquery pack validation", [python, str(SCRIPTS_DIR / "validate_osquery_packs.py")], 300),
        ("cloud guard instance security synthetic contract", [python, str(SCRIPTS_DIR / "validate_cloud_guard_instance_security.py")], 300),
        ("catalog generation", [python, str(SCRIPTS_DIR / "generate_catalog.py")], 300),
        ("dashboard inventory export", [python, str(SCRIPTS_DIR / "deploy_dashboard.py"), "--export-inventory"], 300),
        ("octo apm workshop bundle validation", [python, str(SCRIPTS_DIR / "octo_apm_workshop.py"), "--validate-bundle"], 300),
        ("sentinel strict status", [python, str(SCRIPTS_DIR / "sentinel_conversion_workflow.py"), "status", "--json", "--strict"], 300),
        ("dashboard dry run", [python, str(SCRIPTS_DIR / "deploy_dashboard.py"), "--dry-run", "--skip-live-validation"], 300),
        # Drift check runs AFTER all generators that produce its inputs
        # (catalog.json, dashboard_inventory.json). sentinel_conversion_report.json
        # is not regenerated here — it ships fresh from sentinel_conversion_workflow.py
        # and is treated as an input artifact for the release window.
        ("inventory drift check", [python, str(SCRIPTS_DIR / "check_inventory_drift.py")], 60),
        ("sensitive value scan", [python, str(SCRIPTS_DIR / "scan_sensitive_values.py")], 300),
        ("compileall scripts", [python, "-m", "compileall", "-q", "scripts"], 300),
    ]
    if not skip_tests:
        steps.append(("pytest", [python, "-m", "pytest", "-q"], 1200))
    if include_live:
        parse_path = HEALTH_DIR / "parse-validate-all.json"
        steps.append((
            "live query parse validation",
            [
                python,
                str(SCRIPTS_DIR / "parse_validate_all_queries.py"),
                "--json",
                str(parse_path),
            ],
            1800,
        ))
        verify_path = HEALTH_DIR / "all-dashboard-verify.json"
        steps.append((
            "live profile dashboard verification",
            [
                python,
                str(SCRIPTS_DIR / "verify_deployed_dashboards.py"),
                "--lookback",
                lookback,
                "--query-timeout",
                str(query_timeout),
                "--json",
                str(verify_path),
            ],
            3600,
        ))
    return steps


def _sentinel_backlog_advisory(path: Path = SENTINEL_BACKLOG_PRIORITY_PATH) -> dict:
    if not path.exists():
        return {"available": False, "text": "Sentinel backlog: not ranked"}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"available": False, "text": f"Sentinel backlog: unreadable ({exc})"}
    summary = payload.get("summary", {})
    ranked = int(summary.get("ranked_count", 0) or 0)
    blocker = str(summary.get("top_blocker", "") or "none")
    return {
        "available": True,
        "ranked_count": ranked,
        "top_blocker": blocker,
        "text": f"Sentinel backlog: {ranked} ranked; top blocker: {blocker}",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run release checklist gates")
    parser.add_argument("--include-live", action="store_true", help="Run live dashboard verification for the active OCI_PROFILE")
    parser.add_argument("--skip-tests", action="store_true", help="Skip unittest discovery")
    parser.add_argument("--lookback", default="21d", help="Live verification lookback when --include-live is set")
    parser.add_argument("--query-timeout", type=int, default=60, help="Live query timeout when --include-live is set")
    parser.add_argument("--report", help="Optional release evidence JSON path")
    parser.add_argument("--handoff-summary", action="store_true", help="Write docs/health/latest-handoff.json after a passing run")
    parser.add_argument("--handoff-out", default=str(HEALTH_DIR / "latest-handoff.json"), help="Handoff summary path when --handoff-summary is set")
    args = parser.parse_args()

    HEALTH_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    report_path = Path(args.report) if args.report else HEALTH_DIR / f"release-checklist-{timestamp}.json"

    results = []
    print("=" * 70)
    print("OCI Log Analytics Detection Engine Release Checklist")
    print("=" * 70)
    for name, command, timeout in build_steps(args.include_live, args.skip_tests, args.lookback, args.query_timeout):
        print(f"\n[{len(results) + 1}] {name}")
        result = _run_step(name, command, timeout=timeout)
        results.append(result)
        status = "PASS" if result["ok"] else "FAIL"
        print(f"  {status} exit={result['exit_code']}")
        if not result["ok"]:
            print(result["output_tail"][-2000:])
            break

    report = {
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "include_live": args.include_live,
        "overall_status": "PASS" if all(result["ok"] for result in results) else "FAIL",
        "steps": results,
        "advisories": {
            "sentinel_backlog": _sentinel_backlog_advisory(),
        },
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(report["advisories"]["sentinel_backlog"]["text"])
    print(f"\nRelease evidence: {report_path}")
    if args.handoff_summary and report["overall_status"] == "PASS":
        from handoff_summary import write_summary

        write_summary(report_path, out=Path(args.handoff_out), project_dir=PROJECT_DIR)
        print(f"Handoff summary: {args.handoff_out}")
    return 0 if report["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
