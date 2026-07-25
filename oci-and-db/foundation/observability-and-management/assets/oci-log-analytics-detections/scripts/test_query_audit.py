#!/usr/bin/env python3
"""Tests for live OCI query audit helpers."""

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from query_audit import execute_query, load_specs


class TestQueryAudit(unittest.TestCase):
    """Validate query-audit behavior without hitting OCI."""

    @staticmethod
    def load_query_payload(relative_path: str) -> dict:
        project_dir = Path(__file__).resolve().parent.parent
        with (project_dir / relative_path).open() as handle:
            return json.load(handle)

    def test_load_specs_can_filter_to_detection_rule_eligible_queries(self):
        all_specs = load_specs(False)
        eligible_specs = load_specs(True)

        self.assertGreater(len(all_specs), 0)
        self.assertGreater(len(eligible_specs), 0)
        self.assertLessEqual(len(eligible_specs), len(all_specs))
        self.assertTrue(all(spec["eligible"] for spec in eligible_specs))

    def test_load_specs_can_filter_to_specific_query_files(self):
        specs = load_specs(False, files=[
            "queries/windows_kerberos_pre_authentication_failures.json",
            "windows_ntlm_authentication_failures.json",
        ])

        query_files = {spec["query_file"] for spec in specs}
        self.assertEqual(query_files, {
            "queries/windows_kerberos_pre_authentication_failures.json",
            "queries/windows_ntlm_authentication_failures.json",
        })

    def test_execute_query_returns_error_metadata_instead_of_raising(self):
        class StubClient:
            def query(self, namespace_name, query_details):
                raise RuntimeError("parse failure")

        result = execute_query(StubClient(), "demo-ns", "'Log Source' = 'OCI Audit Logs'", "7d")

        self.assertFalse(result["ok"])
        self.assertEqual(result["rows"], 0)
        self.assertEqual(result["error"], "parse failure")

    @patch("query_audit.oci.log_analytics.models.QueryDetails", autospec=True)
    @patch("query_audit.oci.log_analytics.models.TimeRange", autospec=True)
    def test_execute_query_returns_row_count_for_success(self, mock_time_range, mock_query_details):
        class StubResponse:
            data = type("Data", (), {"items": [{"row": 1}, {"row": 2}, {"row": 3}]})()

        class StubClient:
            def query(self, namespace_name, query_details):
                return StubResponse()

        result = execute_query(StubClient(), "demo-ns", "'Log Source' = 'OCI Audit Logs'", "7d")

        self.assertTrue(result["ok"])
        self.assertFalse(result["empty"])
        self.assertEqual(result["rows"], 3)

    def test_live_eligible_windows_queries_use_string_event_ids(self):
        query_files = [
            "queries/bluelight_screen_capture.json",
            "queries/cmd_suspicious_child_process.json",
            "queries/mimikatz_command_indicators.json",
            "queries/powershell_suspicious_commands.json",
            "queries/hunting/bluelight_apt37_kill_chain.json",
        ]

        for query_file in query_files:
            payload = self.load_query_payload(query_file)
            self.assertNotRegex(payload["query"], r"'Event ID'\s*=\s*\d+", query_file)
            self.assertRegex(payload["query"], r"'Event ID'\s*=\s*'\d+'", query_file)

    def test_sysmon_hunting_queries_use_runtime_mapped_host_fields(self):
        expectations = {
            "queries/bluelight_onedrive_exfiltration.json": "'Host Name'",
            "queries/hunting/dns_exfiltration_entropy.json": "'Host Name (Server)'",
            "queries/hunting/network_c2_beaconing.json": "'Host Name (Server)'",
        }

        for query_file, host_field in expectations.items():
            payload = self.load_query_payload(query_file)
            self.assertIn(host_field, payload["query"], query_file)

    def test_dns_entropy_query_covers_soc_and_native_sysmon_sources(self):
        payload = self.load_query_payload("queries/hunting/dns_exfiltration_entropy.json")

        self.assertIn("'Log Source' = 'SOC Windows Sysmon Logs'", payload["query"])
        self.assertIn("'Log Source' = 'Windows Sysmon Operational Logs'", payload["query"])

    def test_rare_process_hunting_queries_use_bottom_n_stack(self):
        for query_file in [
            "queries/hunting/linux_rare_process.json",
            "queries/hunting/windows_rare_process.json",
        ]:
            payload = self.load_query_payload(query_file)
            self.assertIn("'Process Name' != ''", payload["query"], query_file)
            self.assertIn("| sort executions | head 25", payload["query"], query_file)

    def test_windows_security_command_queries_use_command_line_dimension(self):
        expectations = {
            "queries/cmd_suspicious_child_process.json": "'Command Line'",
            "queries/powershell_suspicious_commands.json": "'Command Line'",
        }

        for query_file, command_field in expectations.items():
            payload = self.load_query_payload(query_file)
            self.assertIn(command_field, payload["query"], query_file)
            self.assertNotIn("by Entity", payload["query"], query_file)
            self.assertNotIn("'Process Name' like '*\\\\", payload["query"], query_file)

    def test_dns_entropy_query_uses_demo_realistic_label_threshold(self):
        payload = self.load_query_payload("queries/hunting/dns_exfiltration_entropy.json")

        self.assertIn("domain_length > 14", payload["query"])

    def test_scanner_stacking_query_tolerates_small_rotating_source_ip_sets(self):
        payload = self.load_query_payload("queries/hunting/web_scanner_tool_stacking.json")

        self.assertIn("requests > 50", payload["query"])
        self.assertIn("source_ips < 5", payload["query"])

    def test_waf_sqli_block_query_uses_sqli_crs_rule_family_only(self):
        payload = self.load_query_payload("queries/waf_sql_injection_attack_blocked.json")
        query = payload["query"]

        self.assertNotIn("'Rule Key' like '*941*'", query)
        self.assertNotIn("'Rule Key' like '*942*'", query)
        self.assertNotIn("'Request URL' like '*/**'", query)
        self.assertIn("'Request URL' like '*UNION%20SELECT*'", query)
        self.assertIn("'Request URL' like '*SLEEP(*'", query)

    def test_windows_event_queries_avoid_unique_on_message_aliases(self):
        for query_file in [
            "queries/windows_audit_policy_changed.json",
            "queries/windows_security_log_cleared_event.json",
        ]:
            payload = self.load_query_payload(query_file)
            self.assertNotIn("unique(msg)", payload["query"], query_file)
            self.assertNotIn("unique(Message)", payload["query"], query_file)

    def test_clickfix_query_uses_parser_tolerant_process_suffixes(self):
        payload = self.load_query_payload("queries/clickfix_fake_captcha_powershell_execution.json")
        query = payload["query"]

        self.assertIn("'Process Name' like '*powershell.exe'", query)
        self.assertIn("'Parent Process Name' like '*chrome.exe'", query)
        self.assertIn("'Log Source' = 'Windows PowerShell Operational Logs'", query)
        self.assertIn("'Script Block Text' like '*ClickFix*'", query)
        self.assertNotIn("'Process Name' like '*\\\\powershell.exe'", query)

    def test_linux_archive_query_uses_targeted_demo_source_and_process_filter(self):
        payload = self.load_query_payload("queries/linux_archive_data_collected_for_exfiltration.json")

        query = payload["query"]
        self.assertIn("'Log Source' = 'SOC Linux Syslog Logs'", query)
        self.assertIn("'Process Name' = 'bash'", query)
        self.assertIn("msg like '*tar*'", query)
        self.assertIn("msg like '*zip*'", query)
        self.assertNotIn("'Log Source' = 'Linux Audit Logs'", query)

    def test_linux_exfiltration_queries_use_targeted_demo_source_and_process_filter(self):
        query_files = [
            "queries/linux_exfiltration_over_alternative_protocol.json",
            "queries/linux_sensitive_data_collection_from_local_system.json",
            "queries/linux_proxy_and_tunneling_tool_detected.json",
            "queries/hunting/linux_persistence_score.json",
        ]

        for query_file in query_files:
            payload = self.load_query_payload(query_file)
            query = payload["query"]

            self.assertIn("'Log Source' = 'SOC Linux Syslog Logs'", query, query_file)
            self.assertIn("'Process Name' = 'bash'", query, query_file)
            self.assertNotIn("'Log Source' = 'Linux Audit Logs'", query, query_file)

    def test_oci_success_status_selectors_include_native_parser_code(self):
        import yaml

        project_dir = Path(__file__).resolve().parent.parent
        # Scan the entire rules/** tree, not just rules/cloud/oci, so a
        # Success-only status selector reintroduced under ANY product (e.g. a
        # future web/load-balancer or app rule) is caught. The dual-Status
        # pattern (`status: [Success, '200']`) is a repo-wide invariant because
        # the native OCI parser projects the HTTP code while SOC custom parsers
        # surface the operator-friendly label.
        rule_dir = project_dir / "rules"
        failures = []

        def check_status_values(path, value_path, value):
            if value == "Success":
                failures.append(f"{path.name}:{value_path} uses Success without '200'")
            elif isinstance(value, list) and "Success" in value and "200" not in value:
                failures.append(f"{path.name}:{value_path} includes Success without '200'")

        def walk_status_values(path, obj, value_path="detection"):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    child_path = f"{value_path}.{key}"
                    if key == "status":
                        check_status_values(path, child_path, value)
                    walk_status_values(path, value, child_path)
            elif isinstance(obj, list):
                for index, value in enumerate(obj):
                    walk_status_values(path, value, f"{value_path}[{index}]")

        rule_files = sorted(rule_dir.rglob("*.yaml")) + sorted(rule_dir.rglob("*.yml"))
        for rule_path in rule_files:
            with rule_path.open() as handle:
                payload = yaml.safe_load(handle)
            if not isinstance(payload, dict):
                continue
            walk_status_values(rule_path, payload.get("detection", {}))

        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
