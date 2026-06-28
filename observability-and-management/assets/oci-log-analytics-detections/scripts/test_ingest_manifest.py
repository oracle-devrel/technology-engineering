#!/usr/bin/env python3
"""Unit tests for ingestion manifest coverage."""

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ingest_test_data import OPTIONAL_UPLOAD_MANIFEST, UPLOAD_MANIFEST, selected_upload_manifest
from oci_config import SOURCE_CANDIDATE_GROUPS, TEST_DATA_DIR, TEST_DATA_FILES


class TestIngestManifest(unittest.TestCase):
    """Ensure all checked-in NDJSON datasets are wired into ingestion."""

    optional_files = {entry["filename"] for entry in OPTIONAL_UPLOAD_MANIFEST}

    def test_manifest_covers_all_checked_in_jsonl_files(self):
        checked_in = sorted(
            path.name for path in Path(TEST_DATA_DIR).glob("*.jsonl")
            if path.name not in self.optional_files
        )
        manifest_files = sorted(entry["filename"] for entry in UPLOAD_MANIFEST)

        self.assertEqual(sorted(TEST_DATA_FILES), checked_in)
        self.assertEqual(manifest_files, checked_in)

    def test_sysmon_network_prefers_dedicated_network_source(self):
        entry = next(item for item in UPLOAD_MANIFEST if item["filename"] == "sysmon_network.jsonl")

        self.assertEqual(entry["source_candidates"], SOURCE_CANDIDATE_GROUPS["sysmon_network"])
        self.assertEqual(entry["source_candidates"][0], "SOC Sysmon Network Logs")
        self.assertIn("Windows Sysmon Operational Logs", entry["source_candidates"])

    def test_windows_security_and_operational_logs_prefer_json_parsers(self):
        winsec_entry = next(item for item in UPLOAD_MANIFEST if item["filename"] == "windows_event_security.jsonl")
        sysmon_op_entry = next(item for item in UPLOAD_MANIFEST if item["filename"] == "sysmon_operational.jsonl")

        self.assertEqual(winsec_entry["source_candidates"], SOURCE_CANDIDATE_GROUPS["windows_event_security"])
        self.assertEqual(winsec_entry["source_candidates"][0], "Windows Event Security Logs")
        self.assertEqual(sysmon_op_entry["source_candidates"], SOURCE_CANDIDATE_GROUPS["sysmon_operational"])
        self.assertEqual(sysmon_op_entry["source_candidates"][0], "Windows Sysmon Operational Logs")

    def test_waf_and_lb_prefer_soc_json_sources_for_direct_uploads(self):
        waf_entry = next(item for item in UPLOAD_MANIFEST if item["filename"] == "waf_security.jsonl")
        lb_entry = next(item for item in UPLOAD_MANIFEST if item["filename"] == "lb_access.jsonl")

        self.assertEqual(waf_entry["source_candidates"][0], "SOC WAF Security Logs")
        self.assertEqual(lb_entry["source_candidates"][0], "SOC Load Balancer Access Logs")

    def test_application_logs_are_wired_to_dedicated_source(self):
        entry = next(item for item in UPLOAD_MANIFEST if item["filename"] == "application_logs.jsonl")

        self.assertEqual(entry["source_candidates"], SOURCE_CANDIDATE_GROUPS["application_logs"])
        self.assertEqual(entry["source_candidates"], ["SOC Application Logs"])
        self.assertIn("application_logs.jsonl", TEST_DATA_FILES)

    def test_selected_upload_manifest_filters_by_filename(self):
        selected = selected_upload_manifest(["application_logs.jsonl"])

        self.assertEqual([entry["filename"] for entry in selected], ["application_logs.jsonl"])
        self.assertEqual(selected[0]["upload_name"], "soc-test-application")

    def test_selected_upload_manifest_rejects_unknown_filename(self):
        with self.assertRaisesRegex(ValueError, "unknown.jsonl"):
            selected_upload_manifest(["unknown.jsonl"])

    def test_vcn_and_network_firewall_logs_are_wired_to_dedicated_sources(self):
        expected = [
            ("vcn_flow.jsonl", "vcn_flow", "SOC VCN Flow Logs"),
            ("network_firewall.jsonl", "network_firewall", "SOC Network Firewall Logs"),
        ]

        for filename, source_key, preferred_source in expected:
            with self.subTest(filename=filename):
                entry = next(item for item in UPLOAD_MANIFEST if item["filename"] == filename)

                self.assertIn(filename, TEST_DATA_FILES)
                self.assertEqual(entry["source_candidates"], SOURCE_CANDIDATE_GROUPS[source_key])
                self.assertEqual(entry["source_candidates"][0], preferred_source)
                self.assertTrue(entry["stream_key"].startswith("soc-detection-"))

    def test_manifest_json_matches_checked_in_files_and_counts(self):
        manifest_path = Path(TEST_DATA_DIR) / "manifest.json"
        checked_in_files = sorted(
            path.name for path in Path(TEST_DATA_DIR).glob("*.jsonl")
            if path.name not in self.optional_files
        )

        with manifest_path.open() as f:
            manifest = __import__("json").load(f)

        manifest_files = sorted(
            filename for filename in manifest["files"]
            if filename not in self.optional_files
        )
        self.assertEqual(manifest_files, checked_in_files)

        total_events = 0
        for filename in checked_in_files:
            with (Path(TEST_DATA_DIR) / filename).open() as f:
                count = sum(1 for line in f if line.strip())
            self.assertEqual(manifest["files"][filename]["event_count"], count, filename)
            total_events += count

        manifest_total = sum(item["event_count"] for item in manifest["files"].values())
        self.assertGreaterEqual(manifest_total, total_events)
        self.assertEqual(manifest["total_events"], manifest_total)


if __name__ == "__main__":
    unittest.main()
