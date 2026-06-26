#!/usr/bin/env python3
"""Tests for Atomic Red Team mapping helpers."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from map_atomic_tests import enrich_queries, generate_coverage_report


class TestAtomicRedTeamMapping(unittest.TestCase):
    """Validate ART enrichment behavior without touching repo queries."""

    @staticmethod
    def write_query(path: Path, *, atomic_red_team=None, techniques=None, product="windows", title=None):
        payload = {
            "title": title or path.stem,
            "logsource": {"product": product},
            "mitre_attack": {"techniques": techniques or ["T1059.003"]},
            "query": "'Log Source' = 'SOC Windows Sysmon Logs'",
        }
        if atomic_red_team is not None:
            payload["atomic_red_team"] = atomic_red_team

        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def test_missing_only_enriches_missing_queries_without_rewriting_existing(self):
        existing_art = {
            "has_tests": False,
            "test_count": 0,
            "techniques_with_tests": [],
            "tests": [],
        }
        art_index = {
            "T1059.003": [{
                "technique_id": "T1059.003",
                "tactic": "execution",
                "technique_name": "Windows Command Shell",
                "test_number": "1",
                "test_name": "Command Prompt",
                "test_guid": "11111111-1111-1111-1111-111111111111",
                "executor": "command_prompt",
            }]
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            query_dir = Path(temp_dir)
            missing_path = query_dir / "missing.json"
            existing_path = query_dir / "existing.json"
            self.write_query(missing_path)
            self.write_query(existing_path, atomic_red_team=existing_art)
            original_existing = existing_path.read_text(encoding="utf-8")

            with patch("map_atomic_tests.QUERIES_DIR", query_dir):
                stats = enrich_queries(art_index, missing_only=True)

            enriched = json.loads(missing_path.read_text(encoding="utf-8"))
            self.assertTrue(enriched["atomic_red_team"]["has_tests"])
            self.assertEqual(enriched["atomic_red_team"]["test_count"], 1)
            self.assertEqual(existing_path.read_text(encoding="utf-8"), original_existing)
            self.assertEqual(stats["enriched"], 1)
            self.assertEqual(stats["already_has"], 1)

    def test_generate_coverage_report_uses_temp_docs_and_ignores_generated_artifacts(self):
        art_field = {
            "has_tests": True,
            "test_count": 1,
            "techniques_with_tests": ["T1059.003"],
            "tests": [{
                "technique_id": "T1059.003",
                "test_name": "Command Prompt",
                "test_guid": "11111111-1111-1111-1111-111111111111",
                "executor": "command_prompt",
                "match_type": "exact",
                "url": "https://example.invalid/T1059.003",
            }],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            queries_dir = root / "queries"
            docs_dir = root / "docs"
            queries_dir.mkdir()

            self.write_query(
                queries_dir / "windows_with_art.json",
                atomic_red_team=art_field,
                product="windows",
                title="Windows With ART",
            )
            self.write_query(
                queries_dir / "linux_without_art.json",
                product="linux",
                techniques=["T1565.001"],
                title="Linux Without ART",
            )
            self.write_query(
                queries_dir / "oci_not_testable.json",
                product="oci",
                title="OCI Not Testable",
            )
            (queries_dir / "catalog.json").write_text(json.dumps({
                "title": "Generated Catalog",
                "logsource": {"product": "windows"},
                "query": "not a saved search",
            }), encoding="utf-8")

            report_path = generate_coverage_report({}, queries_dir=queries_dir, docs_dir=docs_dir)

            self.assertEqual(report_path, docs_dir / "ART_COVERAGE_REPORT.md")
            report = report_path.read_text(encoding="utf-8")
            self.assertIn("**1/2** testable rules have ART tests", report)
            self.assertIn("| Windows | 1 | 1 | 100% | 1 |", report)
            self.assertIn("| Linux | 1 | 0 | 0% | 0 |", report)
            self.assertIn("## Rules Without ART Tests", report)
            self.assertIn("| Linux Without ART | linux | T1565.001 |", report)
            self.assertNotIn("Generated Catalog", report)
            self.assertFalse((root / "ART_COVERAGE_REPORT.md").exists())


if __name__ == "__main__":
    unittest.main()
