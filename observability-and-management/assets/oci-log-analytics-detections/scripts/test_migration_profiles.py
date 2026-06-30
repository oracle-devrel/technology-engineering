#!/usr/bin/env python3
"""Tests for profile-aware Sentinel mapping behavior."""

from __future__ import annotations

import unittest

from scripts.convert_sentinel_kql import (
    apply_mapping_profile,
    load_mapping_config,
    load_mapping_profile,
    rank_candidates,
)


class TestMigrationProfiles(unittest.TestCase):
    def test_same_table_maps_differently_by_profile(self):
        base_mapping = load_mapping_config()
        azure = apply_mapping_profile(base_mapping, load_mapping_profile("azure_as_is"))
        oci = apply_mapping_profile(base_mapping, load_mapping_profile("oci_native"))

        self.assertIn("Azure Entra ID Sign-in Logs", azure["tables"]["SigninLogs"]["sources"])
        self.assertIn("OCI Audit Logs", oci["tables"]["SigninLogs"]["sources"])
        self.assertNotEqual(
            azure["tables"]["SigninLogs"]["sources"],
            oci["tables"]["SigninLogs"]["sources"],
        )

    def test_discovery_evidence_increases_ranking(self):
        mapping = load_mapping_config()
        low = {"title": "Low", "severity": "medium", "query": "SigninLogs | where UserPrincipalName == 'a'"}
        high = {
            "title": "High",
            "severity": "medium",
            "query": "SigninLogs | where UserPrincipalName == 'a'",
            "discovery_evidence_score": 1400,
        }

        ranked = rank_candidates([low, high], mapping)

        self.assertEqual(ranked[0]["title"], "High")

    def test_oci_native_endpoint_sources_include_parser_ready_workload_sources(self):
        mapping = apply_mapping_profile(load_mapping_config(), load_mapping_profile("oci_native"))

        sources = mapping["tables"]["DeviceEvents"]["sources"]

        self.assertIn("SOC Cloud Guard Instance Security Logs", sources)
        self.assertIn("SOC OSQuery Result Logs", sources)


if __name__ == "__main__":
    unittest.main()
