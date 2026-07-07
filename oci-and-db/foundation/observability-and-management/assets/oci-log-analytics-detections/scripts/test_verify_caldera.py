#!/usr/bin/env python3
"""Unit tests for the Caldera verification query contract."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oci_config import SOURCE_CANDIDATE_GROUPS
from verify_caldera_detections import build_log_source_clause, build_operation_queries


class TestVerifyCalderaQueries(unittest.TestCase):
    """Ensure verification queries follow the runtime source-candidate model."""

    def test_build_log_source_clause_includes_all_candidates(self):
        clause = build_log_source_clause("windows_sysmon")

        self.assertTrue(clause.startswith("("))
        self.assertIn(" or ", clause)
        for candidate in SOURCE_CANDIDATE_GROUPS["windows_sysmon"]:
            self.assertIn(f"'Log Source' = '{candidate}'", clause)

    def test_discovery_queries_cover_soc_and_native_windows_sources(self):
        queries = build_operation_queries("discovery")

        self.assertEqual(len(queries), 3)
        for query in queries:
            self.assertIn("'Command Line' like '*", query)
            for candidate in SOURCE_CANDIDATE_GROUPS["windows_sysmon"]:
                self.assertIn(candidate, query)

    def test_exfiltration_queries_use_sysmon_network_candidates(self):
        query = build_operation_queries("exfiltration")[0]

        self.assertIn("'Query Name' like '*.*.*.*.*'", query)
        for candidate in SOURCE_CANDIDATE_GROUPS["sysmon_network"]:
            self.assertIn(candidate, query)


if __name__ == "__main__":
    unittest.main()
