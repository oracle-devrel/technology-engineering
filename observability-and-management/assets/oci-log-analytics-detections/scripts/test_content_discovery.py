#!/usr/bin/env python3
"""Tests for the threat-intel/content discovery pipeline."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from content_discovery import (  # noqa: E402
    classify_candidate,
    deduplicate_candidates,
    normalize_csp_pattern,
    normalize_sigma_rule,
)


class TestContentDiscovery(unittest.TestCase):
    """Validate candidate normalization, dedupe, and classification."""

    def test_normalize_sigma_rule_extracts_candidate_contract(self):
        rule = {
            "id": "sigma-test-001",
            "title": "Suspicious PowerShell Download",
            "description": "Detects PowerShell download cradle behavior.",
            "references": ["https://example.test/rule"],
            "logsource": {"product": "windows", "category": "process_creation"},
            "tags": ["attack.execution", "attack.t1059.001"],
            "detection": {
                "selection": {
                    "Image|endswith": "\\powershell.exe",
                    "CommandLine|contains": "DownloadString",
                },
                "condition": "selection",
            },
            "level": "high",
        }

        candidate = normalize_sigma_rule(rule, local_reference="rules/windows/example.yml")

        self.assertEqual(candidate["title"], "Suspicious PowerShell Download")
        self.assertEqual(candidate["sigma_id"], "sigma-test-001")
        self.assertEqual(candidate["affected_platform"], "windows")
        self.assertIn("T1059.001", candidate["mitre_techniques"])
        self.assertIn("CommandLine", candidate["required_fields"])
        self.assertIn("Windows Sysmon Events", candidate["candidate_log_sources"])
        self.assertEqual(candidate["review_status"], "candidate")

    def test_deduplicate_candidates_prefers_sigma_id_and_merges_sources(self):
        first = {
            "title": "Duplicate Rule",
            "sigma_id": "same-id",
            "source_type": "sigmahq",
            "source_url": "https://example.test/a",
            "mitre_techniques": ["T1059"],
            "candidate_log_sources": ["SOC Windows Sysmon Logs"],
            "required_fields": ["Image"],
        }
        second = {
            "title": "Duplicate Rule Copy",
            "sigma_id": "same-id",
            "source_type": "internal_workshop",
            "source_url": "https://example.test/b",
            "mitre_techniques": ["T1059.001"],
            "candidate_log_sources": ["Windows Sysmon Events"],
            "required_fields": ["CommandLine"],
        }

        deduped = deduplicate_candidates([first, second])

        self.assertEqual(len(deduped), 1)
        self.assertIn("internal_workshop", deduped[0]["source_types"])
        self.assertIn("T1059.001", deduped[0]["mitre_techniques"])
        self.assertIn("CommandLine", deduped[0]["required_fields"])

    def test_classify_candidate_marks_missing_fields(self):
        candidate = {
            "title": "Needs Parser Field",
            "candidate_log_sources": ["SOC Windows Sysmon Logs"],
            "required_fields": ["CommandLine", "UnmappedField"],
            "detection_idea": "match suspicious command line",
        }
        dictionary = {
            "fields": [
                {"display_name": "CommandLine", "raw_json_paths": ["$.CommandLine"]},
            ],
            "source_candidate_groups": {"windows_sysmon": ["SOC Windows Sysmon Logs"]},
        }

        result = classify_candidate(candidate, field_dictionary=dictionary)

        self.assertEqual(result["classification"], "needs field mapping")
        self.assertIn("UnmappedField", " ".join(result["classification_reasons"]))

    def test_normalize_csp_pattern_keeps_oci_equivalent(self):
        candidate = normalize_csp_pattern(
            "defense_evasion",
            {
                "pattern": "Flow log deletion/disabled",
                "csp": "AWS,Azure,GCP",
                "technique": "T1562.008",
                "oci_equivalent": "com.oraclecloud.virtualnetwork.deleteflowlog",
            },
        )

        self.assertEqual(candidate["source_type"], "elastic_csp_gap")
        self.assertEqual(candidate["affected_platform"], "oci")
        self.assertIn("OCI Audit Logs", candidate["candidate_log_sources"])
        self.assertIn("com.oraclecloud.virtualnetwork.deleteflowlog", candidate["detection_idea"])


if __name__ == "__main__":
    unittest.main()
