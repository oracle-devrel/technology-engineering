#!/usr/bin/env python3
"""Tests for handoff summary generation."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import handoff_summary
import release_checklist
from handoff_summary import HandoffError, build_summary, discover_latest_release_report


def write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


class HandoffFixture:
    def __init__(self, root: Path):
        self.root = root
        self.health = root / "docs" / "health"
        self.planning = root / ".planning"
        self.queries = root / "queries"
        self.health.mkdir(parents=True, exist_ok=True)
        self.planning.mkdir(parents=True, exist_ok=True)
        self.queries.mkdir(parents=True, exist_ok=True)

    def write_state(self):
        (self.planning / "STATE.md").write_text(
            """---
status: in_progress
milestone: v1.0
progress:
  total_phases: 5
  completed_phases: 4
  percent: 80
---

# Project State

## Current Position

Phase: 05 (release-and-security-automation) - PLANNED
Plan: 2 of 3
Status: Running Phase 5
""",
            encoding="utf-8",
        )
        (self.planning / "ROADMAP.md").write_text(
            """# Roadmap

- [x] **Phase 1: Baseline**
- [x] **Phase 2: Integrity**
- [ ] **Phase 5: Release and Security Automation**

Plans:
- [x] 05-01: Align release checklist.
- [x] 05-02: Add scanner.
- [ ] 05-03: Add handoff summary.
""",
            encoding="utf-8",
        )

    def write_artifacts(self):
        write_json(
            self.queries / "catalog.json",
            {
                "total_rules": 10,
                "total_content_items": 15,
                "inventory": {
                    "source_yaml_rules": 9,
                    "total_query_artifacts": 15,
                    "generated_sentinel_queries": 3,
                },
            },
        )
        write_json(
            self.queries / "dashboard_inventory.json",
            {"summary": {"total_dashboards": 4, "total_widgets": 22, "advanced_visualization_widgets": 5}},
        )
        write_json(
            self.queries / "sentinel_conversion_report.json",
            {"summary": {"promoted_count": 3, "live_validation_passed": 3, "live_validation_failed": 1}},
        )
        write_json(
            self.queries / "log_source_field_dictionary.json",
            {"summary": {"total_fields": 31, "parser_count": 6, "source_count": 5}},
        )
        write_json(
            self.queries / "octo_apm_workshop_bundle.json",
            {
                "dashboard": {"widget_count": 7},
                "queries": [{"query_file": "apps/example.json"}, {"query_file": "apps/example_2.json"}],
                "detection_rules": {"spec_count": 2, "deployable_count": 2},
            },
        )

    def write_release(self, name: str, *, status: str = "PASS", include_live: bool = False, generated_at: str = "2026-05-15T00:00:00+00:00") -> Path:
        return write_json(
            self.health / name,
            {
                "version": "1.0",
                "generated_at": generated_at,
                "include_live": include_live,
                "overall_status": status,
                "steps": [
                    {
                        "name": "sensitive value scan",
                        "command": ["python3", "scripts/scan_sensitive_values.py"],
                        "started_at": generated_at,
                        "exit_code": 0 if status == "PASS" else 1,
                        "ok": status == "PASS",
                        "output_tail": "ocid1.tenancy.oc1..aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                    }
                ],
            },
        )


class TestHandoffSummary(unittest.TestCase):
    def test_explicit_release_report_extracts_state_and_artifact_counts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = HandoffFixture(Path(temp_dir))
            fixture.write_state()
            fixture.write_artifacts()
            report = fixture.write_release("release-checklist-explicit.json")

            summary = build_summary(report, project_dir=fixture.root)

        self.assertEqual("PASS", summary["release"]["overall_status"])
        self.assertFalse(summary["release"]["include_live"])
        self.assertEqual(1, summary["release"]["local_step_count"])
        self.assertEqual("05 (release-and-security-automation) - PLANNED", summary["gsd_state"]["phase"])
        self.assertEqual(4, summary["artifacts"]["dashboard_inventory"]["total_dashboards"])
        self.assertEqual(31, summary["artifacts"]["field_dictionary"]["total_fields"])
        self.assertEqual(2, summary["artifacts"]["octo_apm_workshop_bundle"]["deployable_detection_rules"])

    def test_latest_release_report_discovery_uses_generated_at(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = HandoffFixture(Path(temp_dir))
            older = fixture.write_release("release-checklist-old.json", generated_at="2026-05-14T23:00:00+00:00")
            newer = fixture.write_release("release-checklist-new.json", generated_at="2026-05-15T01:00:00+00:00")

            discovered = discover_latest_release_report(fixture.health)

        self.assertNotEqual(older, discovered)
        self.assertEqual(newer, discovered)

    def test_summary_excludes_output_tails_and_redacts_sensitive_values(self):
        fixture_ocid = "ocid1.tenancy.oc1..aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"  # scanner-fixture
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = HandoffFixture(Path(temp_dir))
            fixture.write_state()
            fixture.write_artifacts()
            report = fixture.write_release("release-checklist-explicit.json")

            summary = build_summary(report, project_dir=fixture.root)

        serialized = json.dumps(summary)
        self.assertNotIn("output_tail", serialized)
        self.assertNotIn(fixture_ocid, serialized)

    def test_next_command_reflects_live_inclusion(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = HandoffFixture(Path(temp_dir))
            fixture.write_state()
            fixture.write_artifacts()
            local_report = fixture.write_release("release-checklist-local.json", include_live=False)
            live_report = fixture.write_release("release-checklist-live.json", include_live=True)

            local_summary = build_summary(local_report, project_dir=fixture.root)
            live_summary = build_summary(live_report, project_dir=fixture.root)

        self.assertIn("--include-live", local_summary["next_command"])
        self.assertEqual("$gsd-progress", live_summary["next_command"])

    def test_missing_or_failed_release_report_blocks_summary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = HandoffFixture(Path(temp_dir))
            fixture.write_state()
            fixture.write_artifacts()
            failed_report = fixture.write_release("release-checklist-failed.json", status="FAIL")

            with self.assertRaises(HandoffError):
                build_summary(fixture.health / "missing.json", project_dir=fixture.root)
            with self.assertRaises(HandoffError):
                build_summary(failed_report, project_dir=fixture.root)

    def test_cli_writes_handoff_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture = HandoffFixture(Path(temp_dir))
            fixture.write_state()
            fixture.write_artifacts()
            report = fixture.write_release("release-checklist-cli.json")
            output = fixture.health / "latest-handoff.json"

            exit_code = handoff_summary.main([
                "--release-report",
                str(report),
                "--out",
                str(output),
                "--project-dir",
                str(fixture.root),
            ])

            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(0, exit_code)
        self.assertEqual("PASS", payload["release"]["overall_status"])

    def test_release_checklist_can_write_handoff_summary_after_passing_run(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "release.json"
            handoff_path = Path(temp_dir) / "handoff.json"
            first_result = {
                "name": "first gate",
                "command": [sys.executable, "-c", "raise SystemExit(0)"],
                "started_at": "2026-05-15T00:00:00+00:00",
                "exit_code": 0,
                "ok": True,
                "output_tail": "",
            }

            with patch.object(
                sys,
                "argv",
                [
                    "release_checklist.py",
                    "--report",
                    str(report_path),
                    "--handoff-summary",
                    "--handoff-out",
                    str(handoff_path),
                ],
            ):
                with patch("release_checklist.build_steps", return_value=[("first gate", first_result["command"], 30)]):
                    with patch("release_checklist._run_step", return_value=first_result):
                        with patch("handoff_summary.write_summary", return_value={"version": "1.0"}) as write_summary:
                            exit_code = release_checklist.main()

        self.assertEqual(0, exit_code)
        write_summary.assert_called_once()


if __name__ == "__main__":
    unittest.main()
