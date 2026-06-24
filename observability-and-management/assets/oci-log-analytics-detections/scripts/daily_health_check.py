#!/usr/bin/env python3
"""Daily health check for the SOC detection deployment.

Runs the full pre-flight cycle and prints a one-page status banner suitable
for a scheduled task or on-demand sanity check:

1. Inventory deployed dashboards (count, broken, duplicates, missing).
2. Smoke-test the BLUELIGHT showcase widgets via ``smoke_test_bluelight``.
3. Run ``verify_deployed_dashboards`` to query every embedded saved search.
4. Emit a JSON report under ``docs/health/`` and a human-readable banner.

Exit codes:
    0 = all dashboards present, all queries returning rows
    1 = at least one MISS (zero-row query) but no errors
    2 = at least one query / dashboard ERROR or missing
    3 = OCI auth or namespace lookup failed before checks completed

Diff / CI-gate mode (``--diff``):
    When ``--diff`` is supplied the script also compares the current run
    against the most recent previous health report found in ``--report-dir``
    (or the path given via ``--previous-run``).  A banner is printed
    showing the direction of change (IMPROVED / UNCHANGED / DEGRADED) and
    any section-level exit-code deltas.  A DEGRADED result causes the
    process to exit with code 2 regardless of the absolute current status,
    making it suitable as a strict CI gate that fails on any regression.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_DIR / "scripts"
HEALTH_DIR = PROJECT_DIR / "docs" / "health"

# Additive structured diagnostics on stderr. Guarded so importing this module
# without scripts/ on sys.path degrades to a stdlib logger rather than failing.
try:
    import sys as _sys
    if str(SCRIPTS_DIR) not in _sys.path:
        _sys.path.insert(0, str(SCRIPTS_DIR))
    from obs_logging import get_logger
    log = get_logger("daily_health_check")
except ImportError:  # pragma: no cover - defensive
    import logging as _logging
    log = _logging.getLogger("daily_health_check")

# Ordered severity: higher index = worse.
_STATUS_RANK: dict[str, int] = {"OK": 0, "MISS": 1, "ERROR": 2}


def _load_report(path: Path) -> dict | None:
    """Load and return a health-report JSON, or *None* on any error."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def _find_latest_report(report_dir: Path) -> Path | None:
    """Return the path to the most recently written health report, or None."""
    candidates = sorted(report_dir.glob("health-*.json"))
    return candidates[-1] if candidates else None


def _exit_code_worsened(prev_code: int | None, curr_code: int | None) -> bool:
    """True if a section's exit code regressed.

    A ``None`` current code (section skipped/absent) is never a regression.
    A missing previous code is treated as a passing baseline (0), so a section
    that newly fails counts as a regression.
    """
    if curr_code is None:
        return False
    baseline = prev_code if prev_code is not None else 0
    return curr_code > baseline


def _diff_banner(prev: dict, curr: dict) -> tuple[str, bool]:
    """Build a human-readable diff banner and return *(text, degraded)*.

    *degraded* is ``True`` when the current overall status is worse than the
    previous one **or any individual section's exit code worsened**. A section
    can regress while the overall status is unchanged or even improves (e.g. one
    section breaks while another recovers), so per-section deltas must drive the
    CI fail signal too — not only the overall rank.
    """
    prev_status = prev.get("overall_status", "UNKNOWN")
    curr_status = curr.get("overall_status", "UNKNOWN")
    prev_ts = prev.get("timestamp", "?")

    prev_rank = _STATUS_RANK.get(prev_status, 99)
    curr_rank = _STATUS_RANK.get(curr_status, 99)
    overall_degraded = curr_rank > prev_rank

    prev_sections = {s["name"]: s for s in prev.get("sections", [])}
    curr_sections = {s["name"]: s for s in curr.get("sections", [])}

    section_lines: list[str] = []
    section_regressed = False
    for name in sorted(set(prev_sections) | set(curr_sections)):
        prc = prev_sections.get(name, {}).get("exit_code")
        crc = curr_sections.get(name, {}).get("exit_code")
        if prc == crc:
            continue
        worsened = _exit_code_worsened(prc, crc)
        section_regressed = section_regressed or worsened
        marker = "  ↓ REGRESSED" if worsened else ""
        section_lines.append(f"  {name}: exit_code {prc} → {crc}{marker}")

    degraded = overall_degraded or section_regressed

    if overall_degraded:
        direction = "DEGRADED ↓"
    elif section_regressed:
        direction = "DEGRADED ↓ (section regression)"
    elif curr_rank < prev_rank:
        direction = "IMPROVED ↑"
    else:
        direction = "UNCHANGED ="

    lines = [
        f"Diff vs {prev_ts}:",
        f"  overall_status: {prev_status} → {curr_status}  [{direction}]",
    ]
    lines.extend(section_lines)

    return "\n".join(lines), degraded


def _run_subprocess(cmd: list[str]) -> tuple[int, str]:
    try:
        result = subprocess.run(
            cmd, cwd=PROJECT_DIR, capture_output=True, text=True,
            check=False, timeout=2400,
        )
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired as exc:
        return 124, f"TIMEOUT after 2400s: {exc}"
    except Exception as exc:  # noqa: BLE001
        return 99, f"EXEC ERROR: {exc}"


def _section(title: str) -> str:
    return f"\n{'=' * 70}\n{title}\n{'=' * 70}\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Daily SOC detection health check")
    parser.add_argument("--lookback", default="21d",
                        help="Lookback for live queries (default: 21d)")
    parser.add_argument("--skip-verify", action="store_true",
                        help="Skip the per-saved-search verification (slow, ~15min)")
    parser.add_argument("--query-timeout", type=int, default=60,
                        help="Per-widget OCI query timeout for the verifier")
    parser.add_argument("--report-dir", default=str(HEALTH_DIR),
                        help="Directory for JSON output. Default: docs/health/")
    parser.add_argument(
        "--diff",
        action="store_true",
        help=(
            "Compare the current run against the most recent previous health "
            "report and emit a degradation banner.  Exits with code 2 if the "
            "overall status is worse than the previous run (CI gate)."
        ),
    )
    parser.add_argument(
        "--previous-run",
        metavar="REPORT_JSON",
        default=None,
        help="Explicit path to the previous health report for --diff comparison.",
    )
    args = parser.parse_args(argv)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"health-{timestamp.replace(':', '')}.json"

    # Capture the previous report *before* this run writes a new one.
    prev_report: dict | None = None
    if args.diff or args.previous_run:
        if args.previous_run:
            prev_report = _load_report(Path(args.previous_run))
        else:
            prev_path = _find_latest_report(report_dir)
            if prev_path is not None:
                prev_report = _load_report(prev_path)

    overall_status = "OK"
    sections: list[dict] = []

    log.info("health_check.start", extra={"lookback": args.lookback, "skip_verify": args.skip_verify})
    print(_section(f"SOC Health Check — {timestamp}"))

    print(_section("[1/3] Dashboard inventory"))
    inventory_json = report_dir / f"inventory-{timestamp.replace(':', '')}.json"
    rc, out = _run_subprocess([
        sys.executable, str(SCRIPTS_DIR / "inventory_dashboards.py"),
        "--json", str(inventory_json),
    ])
    print(out)
    sections.append({"name": "inventory", "exit_code": rc, "output": out[-2000:]})
    if rc != 0:
        overall_status = "ERROR"

    print(_section(f"[2/3] BLUELIGHT smoke test (lookback={args.lookback})"))
    rc, out = _run_subprocess([
        sys.executable, str(SCRIPTS_DIR / "smoke_test_bluelight.py"),
        "--lookback", args.lookback,
    ])
    print(out)
    sections.append({"name": "bluelight_smoke", "exit_code": rc,
                     "output": out[-2000:]})
    if rc == 1 and overall_status == "OK":
        overall_status = "MISS"
    elif rc == 2:
        overall_status = "ERROR"
    elif rc not in (0, 1):
        overall_status = "ERROR"

    if args.skip_verify:
        print(_section("[3/3] Per-widget verifier — SKIPPED"))
        sections.append({"name": "verifier", "exit_code": None,
                         "output": "skipped via --skip-verify"})
    else:
        print(_section(f"[3/3] Per-widget verifier (lookback={args.lookback})"))
        verify_json = report_dir / f"verify-{timestamp.replace(':', '')}.json"
        rc, out = _run_subprocess([
            sys.executable, str(SCRIPTS_DIR / "verify_deployed_dashboards.py"),
            "--lookback", args.lookback,
            "--query-timeout", str(args.query_timeout),
            "--json", str(verify_json),
        ])
        print(out)
        sections.append({"name": "verifier", "exit_code": rc,
                         "output": out[-2000:]})
        if rc == 1 and overall_status == "OK":
            overall_status = "MISS"
        elif rc == 2:
            overall_status = "ERROR"

    report = {
        "timestamp": timestamp,
        "lookback": args.lookback,
        "overall_status": overall_status,
        "sections": sections,
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    log_emit = log.error if overall_status == "ERROR" else (log.warning if overall_status == "MISS" else log.info)
    log_emit("health_check.done", extra={"overall_status": overall_status})
    print(_section(f"Overall status: {overall_status}  (report: {report_path})"))

    # --diff / --previous-run: compare against the previous report.
    degraded = False
    if (args.diff or args.previous_run) and prev_report is not None:
        banner, degraded = _diff_banner(prev_report, report)
        print(_section("Diff vs previous run"))
        print(banner)
    elif (args.diff or args.previous_run) and prev_report is None:
        print(_section("Diff vs previous run"))
        print("No previous report found — this is the baseline run.")

    base_exit = {"OK": 0, "MISS": 1, "ERROR": 2}.get(overall_status, 3)
    # A DEGRADED result promotes the exit code to at least 2 so CI gates fail.
    if degraded:
        return max(base_exit, 2)
    return base_exit


if __name__ == "__main__":
    raise SystemExit(main())
