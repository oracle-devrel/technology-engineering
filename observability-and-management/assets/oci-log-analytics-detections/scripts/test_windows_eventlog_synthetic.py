#!/usr/bin/env python3
"""Tests for official-shaped Windows Event Log synthetic generation."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from windows_eventlog_synthetic import generate_all, validate_files, write_files


class TestWindowsEventLogSynthetic(unittest.TestCase):
    def test_generates_expected_windows_eventlog_streams(self):
        datasets = generate_all()

        self.assertEqual(
            set(datasets),
            {
                "windows_event_security.jsonl",
                "windows_event_system.jsonl",
                "windows_powershell_operational.jsonl",
                "windows_defender_operational.jsonl",
                "sysmon_operational.jsonl",
            },
        )
        self.assertGreaterEqual(len(datasets["windows_event_security.jsonl"]), 10)

    def test_records_preserve_official_event_envelope(self):
        record = generate_all()["windows_event_security.jsonl"][0]

        self.assertIn("Event", record)
        self.assertEqual(record["Event"]["System"]["Provider"]["Name"], "Microsoft-Windows-Security-Auditing")
        self.assertEqual(record["Event"]["System"]["EventID"], str(record["EventID"]))
        self.assertEqual(
            record["Event"]["System"]["TimeCreated"]["SystemTime"],
            record["TimeCreated"],
        )
        event_data = record["Event"]["EventData"]["Data"]
        self.assertTrue(event_data)
        self.assertTrue(all({"Name", "#text"}.issubset(item) for item in event_data))

    def test_parser_aliases_match_existing_log_analytics_queries(self):
        datasets = generate_all()
        security = [
            event for event in datasets["windows_event_security.jsonl"]
            if str(event["EventID"]) == "4771"
        ][0]
        powershell = datasets["windows_powershell_operational.jsonl"][0]
        defender = datasets["windows_defender_operational.jsonl"][0]
        sysmon = datasets["sysmon_operational.jsonl"][0]

        self.assertEqual(security["Source Address"], "192.0.2.45")
        self.assertEqual(security["Target User Name"], "sql_svc")
        self.assertEqual(security["Failure Reason"], "0x18")
        self.assertIn("DownloadString", powershell["Script Block Text"])
        self.assertEqual(defender["Threat Name"], "Trojan:Win32/Synthetic")
        self.assertEqual(sysmon["Event ID"], 29)
        self.assertTrue(sysmon["Target Filename"].endswith("synthetic-viewer.exe"))

    def test_write_and_validate_generated_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            counts = write_files(out_dir, generate_all())
            report = validate_files(out_dir)

            self.assertIn("windows_event_security.jsonl", counts)
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "manifest.json")))
            self.assertFalse(any(report.values()), json.dumps(report, indent=2))


if __name__ == "__main__":
    unittest.main()
