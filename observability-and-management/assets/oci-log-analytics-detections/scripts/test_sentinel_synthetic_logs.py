#!/usr/bin/env python3
"""Tests for Sentinel synthetic log planning."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sentinel_synthetic_logs import (  # noqa: E402
    SourceContract,
    _safe_live_error,
    build_synthetic_event,
    build_synthetic_plan,
    choose_source_contract,
    extract_predicate_values,
    extract_query_sources,
    extract_required_fields,
    load_source_contracts,
    promote_live_results,
)


class TestSentinelSyntheticLogs(unittest.TestCase):
    """Validate parser-aware synthetic log generation helpers."""

    def _candidate(self, **overrides):
        candidate = {
            "sentinel_id": "sentinel-test-001",
            "title": "Synthetic Sentinel Process",
            "description": "Detects process execution for synthetic validation.",
            "severity": "high",
            "query": (
                "DeviceProcessEvents\n"
                "| where FileName == 'cmd.exe'\n"
                "| where ProcessCommandLine contains 'whoami'"
            ),
            "required_data_connectors": [],
            "mitre_attack": {"tactics": ["execution"], "techniques": ["T1059"]},
            "source_path": "Detections/DeviceProcessEvents/Synthetic.yaml",
            "source_url": "https://example.invalid/synthetic.yaml",
            "kind": "analytics_rule",
        }
        return {**candidate, **overrides}

    def test_extracts_sources_fields_and_predicate_values(self):
        query = (
            "('Log Source' = 'SOC Windows Sysmon Logs' or 'Log Source' = 'Windows Security Events') "
            "and ('Command Line' like '*whoami*') and 'Destination Port' = 443 "
            "| stats count as Count by 'Host Name' | where Count > 3"
        )

        self.assertEqual(
            extract_query_sources(query),
            ["SOC Windows Sysmon Logs", "Windows Security Events"],
        )
        self.assertEqual(
            extract_required_fields(query),
            {"Command Line", "Destination Port", "Host Name"},
        )
        values = extract_predicate_values(query)
        self.assertEqual(values["Command Line"], "whoami")
        self.assertEqual(values["Destination Port"], 443)

    def test_predicate_values_merge_repeated_like_terms(self):
        query = (
            "'Log Source' = 'SOC Windows Sysmon Logs' and "
            "'Command Line' != null and 'Command Line' != '' and "
            "'Command Line' like '*stop-service*' and "
            "'Command Line' like '*sql*' and "
            "'Command Line' like '*msexchange*'"
        )

        values = extract_predicate_values(query)

        self.assertEqual(values["Command Line"], "stop-service sql msexchange")

    def test_predicate_values_do_not_merge_or_alternatives(self):
        query = (
            "'Parent Process Name' in ('w3wp.exe', 'beasvc.exe') or "
            "'Parent Process Name' like 'tomcat*' or "
            "'Parent Process Name' in ('httpd.exe') or "
            "Hashes in ('hash-a', 'hash-b') or Hashes in ('hash-c')"
        )

        values = extract_predicate_values(query)

        self.assertEqual(values["Parent Process Name"], "w3wp.exe")
        self.assertEqual(values["Hashes"], "hash-a")

    def test_like_predicate_values_unescape_windows_backslashes(self):
        query = (
            "'Command Line' like "
            "'*set path=%ProgramFiles(x86)%\\\\WinRAR;C:\\\\Program Files\\\\WinRAR;*' and "
            "'Command Line' like '*cd /d %~dp0 & rar.exe e -o+ -r -inul*.rar*'"
        )

        values = extract_predicate_values(query)

        self.assertEqual(
            values["Command Line"],
            "set path=%ProgramFiles(x86)%\\WinRAR;C:\\Program Files\\WinRAR; "
            "cd /d %~dp0 & rar.exe e -o+ -r -inul.rar",
        )

    def test_builtin_predicate_fields_are_required_for_synthetic_logs(self):
        query = "'Log Source' = 'SOC Application Logs' and ('Event Type' like '*ALERT_CENTER*')"

        self.assertEqual(extract_required_fields(query), {"Event Type"})

    def test_choose_source_contract_prefers_existing_complete_parser(self):
        contracts = load_source_contracts()

        contract, missing_fields, missing_sources = choose_source_contract(
            ["Microsoft Defender Email Logs", "SOC Windows Sysmon Logs"],
            {"Command Line", "Process Name"},
            contracts,
        )

        self.assertIsNotNone(contract)
        self.assertEqual(contract.source_display, "SOC Windows Sysmon Logs")
        self.assertEqual(missing_fields, [])
        self.assertEqual(missing_sources, ["Microsoft Defender Email Logs"])

    def test_build_synthetic_event_maps_display_fields_to_raw_paths(self):
        contract = SourceContract(
            source_display="SOC Test Logs",
            parser_name="socTestParser",
            parser_display="SOC Test Parser",
            field_paths={
                "time": ["$.metadata.time"],
                "Command Line": ["$.CommandLine"],
                "Destination Port": ["$.network.destinationPort"],
            },
            example={
                "EventID": "4688",
                "TimeCreated": "2026-01-01T00:00:00.000Z",
                "metadata": {"time": "2026-01-01T00:00:00.000Z"},
            },
        )

        event = build_synthetic_event(
            contract,
            {"Command Line", "Destination Port"},
            {"Command Line": "whoami", "Destination Port": 443},
            {"sentinel_id": "rule-001", "title": "Synthetic Rule"},
        )

        self.assertEqual(event["CommandLine"], "whoami")
        self.assertEqual(event["network"]["destinationPort"], 443)
        self.assertEqual(event["EventID"], "4688")
        self.assertNotEqual(event["TimeCreated"], "2026-01-01T00:00:00.000Z")
        self.assertEqual(event["metadata"]["time"], event["TimeCreated"])
        self.assertTrue(event["sentinelSynthetic"])

    def test_safe_live_error_redacts_oci_identifiers(self):
        text = (
            "GET https://loganalytics.example-1.oci.oraclecloud.com/20200601/"
            "namespaces/tenantnamespace/sources?compartmentId=ocid1.compartment.oc1..abcdef "
            "opc-request-id=REQ123"
        )

        redacted = _safe_live_error(text)

        self.assertNotIn("tenantnamespace", redacted)
        self.assertNotIn("ocid1.compartment", redacted)
        self.assertNotIn("REQ123", redacted)
        self.assertIn("<OCI_ENDPOINT>", redacted)

    def test_build_synthetic_plan_writes_ready_logs_and_explicit_gaps(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            candidates_file = root / "candidates.json"
            data_dir = root / "data"
            plan_path = root / "plan.json"
            candidates_file.write_text(json.dumps({
                "source": {"name": "Microsoft Sentinel"},
                "candidates": [
                    self._candidate(),
                    self._candidate(
                        sentinel_id="sentinel-source-gap",
                        title="Synthetic Entra Gap",
                        query="SigninLogs | where Result != 'Success' and UserPrincipalName has 'admin'",
                        source_path="Detections/SigninLogs/Synthetic.yaml",
                    ),
                ],
            }), encoding="utf-8")

            report = build_synthetic_plan(
                top=2,
                candidates_file=candidates_file,
                data_dir=data_dir,
                plan_path=plan_path,
                progress_interval=-1,
            )

            statuses = {candidate["status"] for candidate in report["candidates"]}
            self.assertIn("synthetic_ready", statuses)
            self.assertIn("source_gap", statuses)
            self.assertEqual(report["summary"]["synthetic_ready"], 1)
            ready = [candidate for candidate in report["candidates"] if candidate["status"] == "synthetic_ready"][0]
            self.assertEqual(ready["selected_source"], "SOC Windows Sysmon Logs")
            self.assertTrue((data_dir / ready["synthetic_file"]).exists())
            self.assertTrue((data_dir / "manifest.json").exists())
            gap = [candidate for candidate in report["candidates"] if candidate["status"] == "source_gap"][0]
            self.assertIn("no existing parser/source contract", gap["gap"]["reason"])
            self.assertIn("confirm OCI source", gap["gap"]["oci_steps"])

    def test_promote_live_results_writes_only_non_empty_passes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            candidates_file = root / "candidates.json"
            plan_path = root / "plan.json"
            live_path = root / "live.json"
            output_dir = root / "sentinel"
            report_path = root / "report.json"
            candidate = self._candidate()
            candidates_file.write_text(json.dumps({
                "source": {"name": "Microsoft Sentinel"},
                "candidates": [candidate],
            }), encoding="utf-8")
            plan_path.write_text(json.dumps({
                "candidates": [{
                    "title": candidate["title"],
                    "sentinel_id": candidate["sentinel_id"],
                    "source_path": candidate["source_path"],
                    "status": "synthetic_ready",
                    "query": "",
                }]
            }), encoding="utf-8")
            live_path.write_text(json.dumps({
                "results": [{
                    "title": candidate["title"],
                    "sentinel_id": candidate["sentinel_id"],
                    "source_path": candidate["source_path"],
                    "ok": True,
                    "rows": 1,
                    "empty": False,
                    "error": "",
                }]
            }), encoding="utf-8")

            result = promote_live_results(
                plan_path=plan_path,
                live_results_path=live_path,
                candidates_file=candidates_file,
                output_dir=output_dir,
                report_path=report_path,
                clean_output=True,
            )

            self.assertEqual(result["promoted"], 1)
            promoted_files = list(output_dir.glob("*.json"))
            self.assertEqual(len(promoted_files), 1)
            payload = json.loads(promoted_files[0].read_text(encoding="utf-8"))
            self.assertEqual(payload["live_validation_status"], "passed")
            self.assertEqual(payload["test_data_coverage"], "synthetic_live_hit")
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["summary"]["promoted_count"], 1)
            self.assertEqual(report["summary"]["live_validation_passed"], 1)


if __name__ == "__main__":
    unittest.main()
