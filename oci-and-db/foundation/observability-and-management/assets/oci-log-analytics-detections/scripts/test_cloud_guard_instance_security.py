#!/usr/bin/env python3
"""Tests for Cloud Guard Instance Security and OSQuery result contracts."""

from __future__ import annotations

import unittest

from scripts.generate_test_logs import generate_cloud_guard_instance_security_events
from scripts.oci_config import SOURCE_CANDIDATE_GROUPS
from scripts.setup_log_sources import CGIS_FIELD_MAPPINGS, CGIS_SOURCE_DISPLAY, OSQUERY_SOURCE_DISPLAY
from scripts.validate_osquery_packs import REQUIRED_PACKS, load_packs, validate_packs


class TestCloudGuardInstanceSecurity(unittest.TestCase):
    def test_parser_source_field_map_covers_required_osquery_fields(self):
        mapped = {field for field, _path, _sequence in CGIS_FIELD_MAPPINGS}

        for field in {
            "Pack Name",
            "Pack Query ID",
            "Pack Query Name",
            "Finding Severity",
            "OSQuery Query",
            "OSQuery SQL",
            "OSQuery Finding",
            "Process Command Line",
            "Instance OCID",
        }:
            self.assertIn(field, mapped)

    def test_source_candidate_group_keeps_cgis_separate(self):
        candidates = SOURCE_CANDIDATE_GROUPS["cloud_guard_instance_security"]

        self.assertEqual(candidates[0], CGIS_SOURCE_DISPLAY)
        self.assertIn(OSQUERY_SOURCE_DISPLAY, candidates)
        self.assertNotIn("SOC Application Logs", candidates)

    def test_synthetic_dataset_contract(self):
        events = generate_cloud_guard_instance_security_events()

        self.assertGreaterEqual(len(events), 4)
        self.assertTrue(all(event["logType"] == "cloud_guard_instance_security" for event in events))
        self.assertTrue(all(event["osquery"]["sql"].lower().startswith("select") for event in events))

    def test_osquery_pack_schema(self):
        packs = load_packs()
        names = {pack["name"] for pack in packs}

        self.assertEqual(validate_packs(packs), [])
        self.assertTrue(REQUIRED_PACKS.issubset(names))


if __name__ == "__main__":
    unittest.main()
