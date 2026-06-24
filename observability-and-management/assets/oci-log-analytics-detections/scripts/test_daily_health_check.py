"""Focused tests for daily_health_check.py --diff capability.

These tests exercise the diff helpers directly (no OCI calls required).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from scripts.daily_health_check import (  # noqa: E402
    _diff_banner,
    _find_latest_report,
    _load_report,
    _STATUS_RANK,
)


# ---------------------------------------------------------------------------
# _STATUS_RANK
# ---------------------------------------------------------------------------

def test_status_rank_ordering() -> None:
    assert _STATUS_RANK["OK"] < _STATUS_RANK["MISS"] < _STATUS_RANK["ERROR"]


# ---------------------------------------------------------------------------
# _load_report
# ---------------------------------------------------------------------------

def test_load_report_valid(tmp_path: Path) -> None:
    data = {"overall_status": "OK", "timestamp": "2026-01-01T00:00:00Z", "sections": []}
    report_file = tmp_path / "health-20260101T000000Z.json"
    report_file.write_text(json.dumps(data), encoding="utf-8")
    loaded = _load_report(report_file)
    assert loaded == data


def test_load_report_missing_returns_none(tmp_path: Path) -> None:
    assert _load_report(tmp_path / "nonexistent.json") is None


def test_load_report_invalid_json_returns_none(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("not json", encoding="utf-8")
    assert _load_report(bad) is None


# ---------------------------------------------------------------------------
# _find_latest_report
# ---------------------------------------------------------------------------

def test_find_latest_report_returns_none_for_empty_dir(tmp_path: Path) -> None:
    assert _find_latest_report(tmp_path) is None


def test_find_latest_report_picks_lexicographically_last(tmp_path: Path) -> None:
    for ts in ("20260101T000000Z", "20260102T000000Z", "20260103T000000Z"):
        (tmp_path / f"health-{ts}.json").write_text("{}", encoding="utf-8")
    found = _find_latest_report(tmp_path)
    assert found is not None
    assert "20260103" in found.name


# ---------------------------------------------------------------------------
# _diff_banner
# ---------------------------------------------------------------------------

def _make_report(status: str, timestamp: str = "2026-01-01T00:00:00Z",
                 sections: list | None = None) -> dict:
    return {
        "overall_status": status,
        "timestamp": timestamp,
        "sections": sections or [],
    }


def test_diff_banner_unchanged() -> None:
    prev = _make_report("OK")
    curr = _make_report("OK")
    banner, degraded = _diff_banner(prev, curr)
    assert not degraded
    assert "UNCHANGED" in banner
    assert "OK" in banner


def test_diff_banner_improved() -> None:
    prev = _make_report("ERROR")
    curr = _make_report("OK")
    banner, degraded = _diff_banner(prev, curr)
    assert not degraded
    assert "IMPROVED" in banner


def test_diff_banner_section_regression_with_unchanged_overall() -> None:
    # A section breaks (0 -> 2) while the overall status stays the same: this
    # MUST be reported as degraded, otherwise CI silently passes a regression.
    prev = _make_report("OK", sections=[{"name": "inventory", "exit_code": 0}])
    curr = _make_report("OK", sections=[{"name": "inventory", "exit_code": 2}])
    banner, degraded = _diff_banner(prev, curr)
    assert degraded
    assert "REGRESSED" in banner
    assert "inventory" in banner


def test_diff_banner_section_regression_while_overall_improves() -> None:
    # Overall improves (ERROR -> OK) because one section recovered, but a
    # different section regressed (0 -> 2). The net signal must still be degraded.
    prev = _make_report("ERROR", sections=[
        {"name": "verifier", "exit_code": 2},
        {"name": "inventory", "exit_code": 0},
    ])
    curr = _make_report("OK", sections=[
        {"name": "verifier", "exit_code": 0},
        {"name": "inventory", "exit_code": 2},
    ])
    banner, degraded = _diff_banner(prev, curr)
    assert degraded
    assert "inventory" in banner and "REGRESSED" in banner


def test_diff_banner_skipped_section_is_not_a_regression() -> None:
    # A section going from a passing exit code to skipped (None) is neutral.
    prev = _make_report("OK", sections=[{"name": "verifier", "exit_code": 0}])
    curr = _make_report("OK", sections=[{"name": "verifier", "exit_code": None}])
    _, degraded = _diff_banner(prev, curr)
    assert not degraded


def test_diff_banner_degraded_ok_to_miss() -> None:
    prev = _make_report("OK")
    curr = _make_report("MISS")
    banner, degraded = _diff_banner(prev, curr)
    assert degraded
    assert "DEGRADED" in banner


def test_diff_banner_degraded_ok_to_error() -> None:
    prev = _make_report("OK")
    curr = _make_report("ERROR")
    banner, degraded = _diff_banner(prev, curr)
    assert degraded
    assert "DEGRADED" in banner


def test_diff_banner_section_delta_shown() -> None:
    prev_sections = [{"name": "bluelight_smoke", "exit_code": 0, "output": ""}]
    curr_sections = [{"name": "bluelight_smoke", "exit_code": 1, "output": ""}]
    prev = _make_report("OK", sections=prev_sections)
    curr = _make_report("MISS", sections=curr_sections)
    banner, degraded = _diff_banner(prev, curr)
    assert "bluelight_smoke" in banner
    assert "0" in banner
    assert "1" in banner


def test_diff_banner_unchanged_sections_not_shown() -> None:
    sections = [{"name": "inventory", "exit_code": 0, "output": ""}]
    prev = _make_report("OK", sections=sections)
    curr = _make_report("OK", sections=sections)
    banner, _ = _diff_banner(prev, curr)
    # Unchanged sections should not clutter the banner
    assert "inventory" not in banner


# ---------------------------------------------------------------------------
# main() integration — --diff flag wiring
# ---------------------------------------------------------------------------

def test_main_diff_no_previous_report_exits_ok(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """When --diff is passed but there is no previous report the run still succeeds."""
    import scripts.daily_health_check as dhc

    # Stub all subprocesses so they return OK instantly.
    monkeypatch.setattr(dhc, "_run_subprocess", lambda cmd: (0, "ok"))

    exit_code = dhc.main([
        "--diff",
        "--skip-verify",
        "--report-dir", str(tmp_path),
    ])
    assert exit_code == 0


def test_main_diff_degraded_exits_2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--diff exits with code 2 when the current run is worse than the previous one."""
    import scripts.daily_health_check as dhc

    # Write a previous "OK" report.
    prev_data = {
        "timestamp": "2026-01-01T000000Z",
        "lookback": "21d",
        "overall_status": "OK",
        "sections": [],
    }
    (tmp_path / "health-2026-01-01T000000Z.json").write_text(
        json.dumps(prev_data), encoding="utf-8"
    )

    # This run will be MISS (bluelight returns exit_code 1).
    def _fake_run(cmd: list) -> tuple[int, str]:
        if "smoke_test_bluelight" in " ".join(cmd):
            return 1, "MISS"
        return 0, "ok"

    monkeypatch.setattr(dhc, "_run_subprocess", _fake_run)

    exit_code = dhc.main([
        "--diff",
        "--skip-verify",
        "--report-dir", str(tmp_path),
    ])
    assert exit_code == 2  # degraded: OK → MISS triggers exit 2
