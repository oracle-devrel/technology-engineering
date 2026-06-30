#!/usr/bin/env python3
"""Regression tests for generated application telemetry."""

import os
import random
import sys
import unittest
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_test_logs import generate_application_events


class TestApplicationDataset(unittest.TestCase):
    """Ensure the demo app telemetry can light up the app dashboards."""

    def test_application_events_cover_both_services_and_shared_traces(self):
        random.seed(42)
        events = generate_application_events()

        services = {event["serviceName"] for event in events}
        self.assertIn("enterprise-crm-portal", services)
        self.assertIn("octo-drone-shop", services)

        trace_services = defaultdict(set)
        for event in events:
            if event.get("traceId"):
                trace_services[event["traceId"]].add(event["serviceName"])

        self.assertTrue(
            any(len(seen_services) > 1 for seen_services in trace_services.values()),
            "expected at least one trace_id to span both services",
        )

    def test_application_events_include_browser_and_security_signals(self):
        random.seed(7)
        events = generate_application_events()

        span_attributes = " ".join(event.get("spanAttributes", "") for event in events)
        attack_types = {event.get("securityAttackType") for event in events if event.get("securityAttackType")}

        self.assertIn("canvas.toDataURL", span_attributes)
        self.assertIn("document.cookie", span_attributes)
        self.assertIn("keydown", span_attributes)
        self.assertIn("xss_reflected", attack_types)
        self.assertIn("sqli", attack_types)
        self.assertIn("broken_auth", attack_types)


if __name__ == "__main__":
    unittest.main()
