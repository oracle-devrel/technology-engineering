#!/usr/bin/env python3
"""Tests for Octo APM detection-rule live verification."""

from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import verify_octo_apm_detection_rules as verifier


class TestVerifyOctoApmDetectionRules(unittest.TestCase):
    def test_verify_detection_rules_marks_hits_misses_and_errors(self):
        query_files = ["apps/rule-hit.json", "apps/rule-miss.json", "apps/rule-error.json"]
        responses = [
            {"query_file": query_files[0], "ok": True, "rows": 1, "empty": False, "error": ""},
            {"query_file": query_files[1], "ok": True, "rows": 0, "empty": True, "error": ""},
            {"query_file": query_files[2], "ok": False, "rows": 0, "empty": False, "error": "bad field"},
        ]

        with patch.object(verifier, "DETECTION_RULE_QUERY_FILES", query_files), \
                patch.object(verifier, "get_la_client", return_value=object()), \
                patch.object(verifier, "get_namespace", return_value="ns"), \
                patch.object(verifier, "load_query_info", return_value={"query": "'Log Source' = 'SOC Application Logs'"}), \
                patch.object(verifier, "validate_query_in_oci", side_effect=responses):
            results = verifier.verify_detection_rules("21d", 90)

        self.assertEqual([result["status"] for result in results], ["HIT", "MISS", "ERROR"])


if __name__ == "__main__":
    unittest.main()
