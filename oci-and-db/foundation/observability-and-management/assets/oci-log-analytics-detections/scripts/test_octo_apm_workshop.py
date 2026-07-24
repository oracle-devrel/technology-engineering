#!/usr/bin/env python3
"""Tests for the scoped Octo APM workshop export surface."""

import json
import os
import sys
import unittest
from copy import deepcopy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate_test_logs import generate_application_events
from ingest_test_data import selected_upload_manifest
from octo_apm_workshop import (
    DASHBOARD_NAME,
    OCTO_WORKSHOP_DATA_FILE,
    build_bundle,
    filter_octo_events,
    query_files_for_dashboard,
    validate_bundle,
)


class TestOctoApmWorkshop(unittest.TestCase):
    """Validate that the workshop bundle stays tightly scoped."""

    def test_dashboard_query_scope_is_octo_only(self):
        query_files = query_files_for_dashboard(DASHBOARD_NAME)

        self.assertEqual(len(query_files), 17)
        self.assertTrue(all(path.startswith("apps/apm_octo_") for path in query_files))

    def test_filter_octo_events_keeps_only_octo_namespace(self):
        events = generate_application_events()
        octo_events = filter_octo_events(events)

        self.assertGreater(len(octo_events), 0)
        self.assertTrue(all(event.get("service.namespace") == "octo" for event in octo_events))
        self.assertTrue(any(event.get("db.statement") for event in octo_events))
        self.assertTrue(any(event.get("java_apm.path") for event in octo_events))
        self.assertTrue(any(event.get("security.attack.id") == "attack-octo-demo-001" for event in octo_events))

    def test_upload_manifest_accepts_octo_workshop_file(self):
        manifest = selected_upload_manifest([OCTO_WORKSHOP_DATA_FILE])

        self.assertEqual(len(manifest), 1)
        self.assertEqual(manifest[0]["filename"], OCTO_WORKSHOP_DATA_FILE)
        self.assertEqual(manifest[0]["source_candidates"], ["SOC Application Logs"])

    def test_bundle_contains_only_sanitized_octo_assets(self):
        bundle = build_bundle(generated_at="2026-05-10T00:00:00Z")
        serialized = json.dumps(bundle)

        self.assertEqual(bundle["dashboard"]["name"], DASHBOARD_NAME)
        self.assertEqual(bundle["dashboard"]["widget_count"], 17)
        self.assertTrue(all(widget["query_file"].startswith("apps/apm_octo_") for widget in bundle["dashboard"]["widgets"]))
        self.assertTrue(
            all(widget["time_selection"] == {"timePeriod": "l21d"} for widget in bundle["dashboard"]["widgets"])
        )
        self.assertIn("Trace ID", {field["display_name"] for field in bundle["fields"]})
        self.assertIn("Payment Redirect URL", {field["display_name"] for field in bundle["fields"]})
        self.assertIn("API Gateway Action", {field["display_name"] for field in bundle["fields"]})
        self.assertGreaterEqual(bundle["detection_rules"]["deployable_count"], 4)
        self.assertNotIn("ocid1.", serialized)
        self.assertNotIn("octodemo.cloud", serialized)
        self.assertNotIn("161.153.", serialized)

    def test_validate_bundle_accepts_current_generated_contract(self):
        bundle = build_bundle(generated_at="2026-05-10T00:00:00Z")

        self.assertEqual(validate_bundle(bundle), [])

    def test_validate_bundle_rejects_generated_support_artifact_query_reference(self):
        bundle = build_bundle(generated_at="2026-05-10T00:00:00Z")
        bad_bundle = deepcopy(bundle)
        bad_bundle["queries"][0]["query_file"] = "sentinel_synthetic_plan.json"
        bad_bundle["dashboard"]["widgets"][0]["query_file"] = "octo_apm_workshop_bundle.json"

        errors = validate_bundle(bad_bundle)

        self.assertTrue(
            any("sentinel_synthetic_plan.json" in error and "saved-search query" in error for error in errors),
            errors,
        )
        self.assertTrue(
            any("octo_apm_workshop_bundle.json" in error and "saved-search query" in error for error in errors),
            errors,
        )

    def test_validate_bundle_rejects_sensitive_live_values(self):
        bundle = build_bundle(generated_at="2026-05-10T00:00:00Z")
        bad_bundle = deepcopy(bundle)
        bad_bundle["deployment"]["commands"].append(
            "oci la query --compartment-id ocid1.compartment.oc1..secret --endpoint https://octodemo.cloud"
        )

        errors = validate_bundle(bad_bundle)

        self.assertTrue(any("sensitive live value" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
