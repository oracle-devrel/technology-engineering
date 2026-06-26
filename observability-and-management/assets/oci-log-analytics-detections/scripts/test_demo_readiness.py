#!/usr/bin/env python3
"""Tests for live demo readiness helpers."""

import os
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from demo_readiness import (
    PROVIDER_EXPECTATIONS,
    build_log_source_clause,
    execute_query_check,
    load_query,
)


class TestDemoReadiness(unittest.TestCase):
    """Validate dry-run query composition for tomorrow's demo checks."""

    def test_build_log_source_clause_handles_single_and_multi_source_groups(self):
        self.assertEqual(build_log_source_clause("application_logs"), "'Log Source' = 'SOC Application Logs'")
        clause = build_log_source_clause("cloud_guard")
        self.assertIn("'OCI Cloud Guard Problems'", clause)
        self.assertIn("'SOC Cloud Guard Logs'", clause)

    def test_provider_expectations_cover_all_csp_demos(self):
        self.assertEqual(PROVIDER_EXPECTATIONS, ["OCI", "Azure", "AWS", "GCP"])

    def test_demo_query_loader_reads_observability_queries(self):
        payload = load_query("apps/app_db_performance_correlation.json")
        self.assertIn("oracle_atp", payload["query"])
        self.assertIn("Database Performance Correlation", payload["title"])

    def test_service_health_timeline_uses_supported_timestats_query(self):
        payload = load_query("apps/app_service_health_timeline.json")
        self.assertIn("| timestats span = 15minute count as Events by 'Service Name'", payload["query"])
        self.assertNotIn("timecluster", payload["query"])

    def test_execute_query_check_returns_rows_for_successful_query(self):
        class StubClient:
            def query(self, namespace_name, query_details):
                self.namespace_name = namespace_name
                self.query_details = query_details
                return SimpleNamespace(data=SimpleNamespace(items=[{"Events": 12}, {"Events": 8}]))

        result = execute_query_check(
            StubClient(),
            "demo-ns",
            "'Log Source' = 'SOC Application Logs' | stats count as Events",
            "24h",
            name="Application / Browser Telemetry",
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["rows"], 2)
        self.assertNotIn("error", result)

    def test_execute_query_check_returns_error_instead_of_raising(self):
        class StubClient:
            def query(self, namespace_name, query_details):
                raise RuntimeError("Invalid field for BY: Message.")

        result = execute_query_check(
            StubClient(),
            "demo-ns",
            "'Log Source' = 'SOC Application Logs' | stats count as Events by msg",
            "24h",
            name="Application Service Health Timeline",
            group="performance",
            query_file="apps/app_service_health_timeline.json",
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["rows"], 0)
        self.assertIn("Invalid field for BY: Message.", result["error"])
        self.assertEqual(result["group"], "performance")
        self.assertEqual(result["query_file"], "apps/app_service_health_timeline.json")


if __name__ == "__main__":
    unittest.main()
