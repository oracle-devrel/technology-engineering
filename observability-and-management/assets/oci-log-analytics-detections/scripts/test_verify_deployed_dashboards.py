#!/usr/bin/env python3
"""Unit tests for deployed dashboard verification helpers."""

import os
import sys
import time
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_deployed_dashboards import _run_query


class TestVerifyDeployedDashboards(unittest.TestCase):
    def test_run_query_returns_row_count_for_success(self):
        class StubClient:
            query_details = None

            def query(self, namespace_name, query_details):
                self.query_details = query_details
                return SimpleNamespace(data=SimpleNamespace(items=[{"row": 1}, {"row": 2}]))

        stub = StubClient()
        count, error = _run_query(
            stub,
            "demo-ns",
            "'Log Source' = 'SOC Linux Syslog Logs'",
            datetime.now(timezone.utc),
            datetime.now(timezone.utc),
            timeout=1,
        )

        self.assertEqual(count, 2)
        self.assertIsNone(error)
        self.assertTrue(stub.query_details.compartment_id_in_subtree)

    def test_run_query_returns_error_metadata_for_exceptions(self):
        class StubClient:
            def query(self, namespace_name, query_details):
                raise RuntimeError("query failed")

        count, error = _run_query(
            StubClient(),
            "demo-ns",
            "'Log Source' = 'SOC Linux Syslog Logs'",
            datetime.now(timezone.utc),
            datetime.now(timezone.utc),
            timeout=1,
        )

        self.assertEqual(count, -1)
        self.assertEqual(error, "query failed")

    def test_run_query_enforces_timeout(self):
        class SlowClient:
            def query(self, namespace_name, query_details):
                time.sleep(2)
                return SimpleNamespace(data=SimpleNamespace(items=[{"row": 1}]))

        count, error = _run_query(
            SlowClient(),
            "demo-ns",
            "'Log Source' = 'SOC Linux Syslog Logs'",
            datetime.now(timezone.utc),
            datetime.now(timezone.utc),
            timeout=1,
        )

        self.assertEqual(count, -1)
        self.assertIn("query validation exceeded 1s", error)


if __name__ == "__main__":
    unittest.main()
