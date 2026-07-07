#!/usr/bin/env python3
"""Regression tests for Windows event-log OOTB detection expansion."""

from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import field_dictionary
from generate_test_logs import (
    generate_windows_defender_operational,
    generate_windows_event_security,
    generate_windows_powershell_operational,
)


ROOT = Path(__file__).resolve().parents[1]
QUERIES_DIR = ROOT / "queries"


EXPECTED_OOTB_RULES = {
    "windows_audit_policy_changed.json",
    "windows_security_log_cleared_event.json",
    "windows_scheduled_task_created_or_updated_event.json",
    "windows_service_installed_event_log.json",
    "windows_kerberos_pre_authentication_failures.json",
    "windows_ntlm_authentication_failures.json",
    "windows_admin_share_access_spike_event.json",
    "windows_privileged_group_membership_change_event.json",
    "windows_account_or_group_enumeration_spike.json",
    "windows_powershell_script_block_suspicious_content.json",
    "windows_defender_malware_or_remediation_event.json",
    "sysmon_executable_file_created_or_detected.json",
    "clickfix_fake_captcha_powershell_execution.json",
}


class TestWindowsEventLogOotbRules(unittest.TestCase):
    def test_expected_query_files_exist_and_are_detection_surface(self):
        missing = [
            filename
            for filename in sorted(EXPECTED_OOTB_RULES)
            if not (QUERIES_DIR / filename).exists()
        ]
        self.assertEqual(missing, [])

        for filename in sorted(EXPECTED_OOTB_RULES):
            payload = json.loads((QUERIES_DIR / filename).read_text())
            self.assertIn("query", payload)
            self.assertNotEqual(payload.get("type"), "hunting")
            self.assertTrue(payload.get("mitre_attack", {}).get("techniques"))
            self.assertTrue(payload.get("logsource", {}).get("candidates"))

    def test_query_fields_are_backed_by_generated_dictionary(self):
        dictionary = field_dictionary.build_field_dictionary()
        for filename in sorted(EXPECTED_OOTB_RULES):
            payload = json.loads((QUERIES_DIR / filename).read_text())
            errors = field_dictionary.validate_query_field_coverage(
                f"queries/{filename}",
                payload,
                dictionary,
            )
            self.assertEqual(errors, [])

    def test_windows_security_parser_covers_pdf_driven_fields(self):
        dictionary = field_dictionary.build_field_dictionary()
        fields = {
            field["display_name"]
            for field in dictionary["fields"]
            if any(
                source["source_display"] == "Windows Event Security Logs"
                for source in field.get("sources", [])
            )
        }
        self.assertTrue({
            "Access Mask",
            "Failure Reason",
            "Object Name",
            "Relative Target Name",
            "Service File Name",
            "Share Name",
            "Task Name",
        }.issubset(fields))

    def test_synthetic_event_streams_include_native_detection_events(self):
        security_events = generate_windows_event_security()
        powershell_events = generate_windows_powershell_operational()
        defender_events = generate_windows_defender_operational()

        security_event_ids = {
            str(event.get("Event ID") or event.get("EventID"))
            for event in security_events
        }
        self.assertTrue({"4719", "4771", "4776", "5140", "5145", "4697", "4702"}.issubset(security_event_ids))

        self.assertTrue(any(
            str(event.get("Event ID") or event.get("EventID")) == "4104"
            and "Script Block Text" in event
            for event in powershell_events
        ))
        self.assertTrue(any(
            str(event.get("Event ID") or event.get("EventID")) in {"1116", "1117", "5007"}
            and "Threat Name" in event
            for event in defender_events
        ))


if __name__ == "__main__":
    unittest.main()
