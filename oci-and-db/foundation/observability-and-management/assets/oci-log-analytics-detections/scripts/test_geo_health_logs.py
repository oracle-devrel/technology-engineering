#!/usr/bin/env python3
"""Regression tests for multicloud geographic health dataset generation."""

import os
import random
import sys
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_geo_health_logs import build_instance_fleet, generate_all_heartbeats


class TestGeoHealthLogs(unittest.TestCase):
    """Ensure generated multicloud health data covers all target providers."""

    def test_instance_fleet_spans_all_clouds(self):
        random.seed(42)
        fleet = build_instance_fleet()
        providers = {instance["cloud_provider"] for instance in fleet}

        self.assertEqual(providers, {"OCI", "Azure", "AWS", "GCP"})

    def test_generated_heartbeats_include_expected_schema_and_aws(self):
        events, fleet = generate_all_heartbeats(interval_minutes=15, duration_minutes=30)
        self.assertGreater(len(events), 0)
        self.assertGreater(len(fleet), 0)

        providers = {event["Cloud Provider"] for event in events}
        self.assertIn("AWS", providers)

        sample = events[0]
        for field in [
            "Timestamp",
            "Cloud Provider",
            "Region",
            "Region Display",
            "Latitude",
            "Longitude",
            "Instance ID",
            "Host Name",
            "Status",
            "Heartbeat Sequence",
            "Log Source",
        ]:
            self.assertIn(field, sample)

        self.assertEqual(sample["Log Source"], "SOC Multicloud Health Logs")

    def test_generated_heartbeats_fill_a_past_time_window(self):
        events, _ = generate_all_heartbeats(interval_minutes=15, duration_minutes=60)

        timestamps = [
            datetime.fromisoformat(event["Timestamp"].replace("Z", "+00:00"))
            for event in events
        ]

        self.assertTrue(timestamps)
        now = datetime.now(timezone.utc)
        self.assertLessEqual(max(timestamps), now)
        self.assertGreaterEqual(min(timestamps), now.replace(microsecond=0) - timedelta(minutes=61))


if __name__ == "__main__":
    unittest.main()
