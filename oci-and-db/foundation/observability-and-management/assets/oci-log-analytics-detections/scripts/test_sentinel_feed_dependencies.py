#!/usr/bin/env python3
"""Tests for Sentinel external feed dependency bundling."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.sentinel_feed_dependencies import build_feed_bundle, validate_feed_bundle


class TestSentinelFeedDependencies(unittest.TestCase):
    def test_build_bundle_dedupes_feeds_and_preserves_candidates(self):
        inventory = {
            "version": "1.0",
            "generated_at": "2026-06-01T00:00:00Z",
            "items": [
                {
                    "content_id": "rule-1",
                    "title": "Rule One",
                    "source_path": "Detections/one.yaml",
                    "feed_dependencies": [
                        {
                            "kind": "externaldata",
                            "name": "iocs",
                            "url": "https://example.test/iocs.csv",
                            "format": "csv",
                            "columns": [{"name": "IoC", "type": "string"}],
                            "options": {"ignoreFirstRecord": "True"},
                            "staging": {"source_candidates": ["Azure Log Analytics Custom Logs"]},
                        }
                    ],
                },
                {
                    "content_id": "rule-2",
                    "title": "Rule Two",
                    "source_path": "Detections/two.yaml",
                    "feed_dependencies": [
                        {
                            "kind": "externaldata",
                            "name": "threatFeed",
                            "url": "https://example.test/iocs.csv",
                            "format": "csv",
                            "columns": [{"name": "IoC", "type": "string"}],
                            "options": {"ignoreFirstRecord": "True"},
                            "staging": {"source_candidates": ["Azure Log Analytics Custom Logs"]},
                        }
                    ],
                },
            ],
        }

        bundle = build_feed_bundle(inventory)

        self.assertEqual(bundle["summary"]["feed_count"], 1)
        self.assertEqual(bundle["summary"]["candidate_count"], 2)
        feed = bundle["feeds"][0]
        self.assertTrue(feed["feed_id"].startswith("feed_"))
        self.assertEqual(feed["url"], "https://example.test/iocs.csv")
        self.assertEqual(feed["target_log_source"], "Azure Log Analytics Custom Logs")
        self.assertEqual([ref["content_id"] for ref in feed["linked_content"]], ["rule-1", "rule-2"])
        self.assertEqual(feed["staging_contract"]["normalized_event_fields"], ["IoC"])

    def test_validate_bundle_flags_missing_required_fields(self):
        errors = validate_feed_bundle({"version": "1.0", "summary": {}, "feeds": [{"url": ""}]})

        self.assertIn("$.feeds[0]: missing feed_id", errors)
        self.assertIn("$.feeds[0]: missing url", errors)

    def test_cli_check_detects_stale_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inventory_path = root / "inventory.json"
            bundle_path = root / "bundle.json"
            inventory_path.write_text(json.dumps({
                "items": [
                    {
                        "content_id": "rule-1",
                        "title": "Rule",
                        "source_path": "Detections/rule.yaml",
                        "feed_dependencies": [
                            {
                                "kind": "externaldata",
                                "name": "iocs",
                                "url": "https://example.test/iocs.csv",
                                "format": "csv",
                                "columns": [{"name": "IoC", "type": "string"}],
                                "options": {},
                            }
                        ],
                    }
                ]
            }), encoding="utf-8")
            bundle_path.write_text(json.dumps({"version": "1.0", "summary": {}, "feeds": []}), encoding="utf-8")

            expected = build_feed_bundle(json.loads(inventory_path.read_text(encoding="utf-8")))
            actual = json.loads(bundle_path.read_text(encoding="utf-8"))

        self.assertNotEqual(expected["summary"], actual["summary"])


if __name__ == "__main__":
    unittest.main()
