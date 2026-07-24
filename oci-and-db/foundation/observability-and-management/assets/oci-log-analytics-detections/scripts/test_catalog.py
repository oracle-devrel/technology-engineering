#!/usr/bin/env python3
"""Unit tests for the catalog generator."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_catalog import (
    TACTIC_DISPLAY,
    TACTIC_ORDER,
    VALID_MITRE_TACTICS,
    generate_json_catalog,
    get_inventory_counts,
    load_query_surfaces,
)


class TestCatalogSurfaces(unittest.TestCase):
    """Validate multi-surface catalog generation."""

    def test_catalog_includes_apps_and_inventory_split(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            queries_dir = project_dir / "queries"
            apps_dir = queries_dir / "apps"
            hunting_dir = queries_dir / "hunting"
            rules_dir = project_dir / "rules" / "web" / "browser_attacks"

            apps_dir.mkdir(parents=True, exist_ok=True)
            hunting_dir.mkdir(parents=True, exist_ok=True)
            rules_dir.mkdir(parents=True, exist_ok=True)

            (queries_dir / "base_detection.json").write_text(json.dumps({
                "title": "Base Detection",
                "query": "'Log Source' = 'OCI Audit Logs'",
                "sigma_id": "sigma-base-001",
                "level": "high",
                "logsource": {"product": "oci", "service": "audit"},
                "mitre_attack": {"tactics": ["initial_access"], "techniques": ["T1078"]},
            }))
            (queries_dir / "sentinel_synthetic_plan.json").write_text(json.dumps({
                "summary": {"synthetic_ready": 1},
                "candidates": [{"title": "Support artifact, not a query"}],
            }))
            (queries_dir / "sentinel_synthetic_live_results.json").write_text(json.dumps({
                "tested": 1,
                "results": [{"title": "Support artifact, not a query", "rows": 1}],
            }))
            (queries_dir / "conversion_examples.json").write_text(json.dumps({
                "schema_version": "1.0.0",
                "examples": [{"title": "Support artifact, not a query"}],
            }))
            (queries_dir / "cross_ql_mapping_patterns.json").write_text(json.dumps({
                "schema_version": "1.0.0",
                "patterns": [{"id": "support-artifact"}],
            }))
            (queries_dir / "logan_ql_reference_catalog.json").write_text(json.dumps({
                "schema_version": "1.0.0",
                "commands": [{"name": "stats"}],
            }))
            (apps_dir / "apm_browser.json").write_text(json.dumps({
                "title": "Browser Detection",
                "query": "'Log Source' = 'SOC Application Logs'",
                "sigma_id": "sigma-browser-001",
                "level": "medium",
                "logsource": {"product": "oci", "service": "apm"},
                "mitre_attack": {"tactics": ["execution"], "techniques": ["T1059.007"]},
            }))
            (apps_dir / "app_health.json").write_text(json.dumps({
                "title": "Curated App Health",
                "query": "'Log Source' = 'SOC Application Logs'",
                "level": "informational",
                "logsource": {"product": "oci", "service": "apm"},
                "mitre_attack": {"tactics": [], "techniques": []},
            }))
            (hunting_dir / "hunt.json").write_text(json.dumps({
                "title": "Threat Hunt",
                "query": "'Log Source' = 'OCI Audit Logs' | stats count",
                "level": "high",
                "mitre_attack": {"tactics": ["discovery"], "techniques": ["T1087.001"]},
                "references": [
                    {
                        "name": "Black Hills InfoSec FreeLabFriday Labs",
                        "url": "https://github.com/blackhillsinfosec/FreeLabFriday_Labs",
                    }
                ],
            }))

            (rules_dir / "apm_browser.yaml").write_text(
                "title: Browser Detection\n"
                "id: sigma-browser-001\n"
                "logsource:\n"
                "  product: oci\n"
                "  service: apm\n"
                "detection:\n"
                "  selection:\n"
                "    HttpUrl|contains: test\n"
                "  condition: selection\n"
            )

            detections, app_queries, hunting = load_query_surfaces(queries_dir, apps_dir, hunting_dir)
            inventory = get_inventory_counts(project_dir, queries_dir, apps_dir, hunting_dir)
            catalog = generate_json_catalog(detections, app_queries, hunting, inventory=inventory)

            self.assertEqual(len(detections), 1)
            self.assertEqual(len(app_queries), 2)
            self.assertEqual(len(hunting), 1)
            self.assertEqual(catalog["total_rules"], 1)
            self.assertEqual(catalog["total_app_queries"], 2)
            self.assertEqual(catalog["total_hunting"], 1)
            self.assertEqual(catalog["inventory"]["source_derived_app_queries"], 1)
            self.assertEqual(catalog["inventory"]["curated_app_queries"], 1)
            self.assertEqual(catalog["inventory"]["generated_sigma_queries"], 2)
            self.assertEqual(len(catalog["app_queries"]), 2)
            self.assertIn("T1059.007", catalog["all_mitre_techniques"])
            self.assertIn("T1087.001", catalog["all_mitre_techniques"])
            self.assertEqual(
                catalog["hunting_queries"][0]["references"][0]["url"],
                "https://github.com/blackhillsinfosec/FreeLabFriday_Labs",
            )

    def test_every_counted_tactic_is_renderable_in_markdown(self):
        """CATALOG.md reports `len(matrix) tactics` in the headline but only renders
        a section per tactic in TACTIC_ORDER. Every canonical tactic must therefore
        be in both TACTIC_ORDER and TACTIC_DISPLAY, otherwise the Markdown would
        count tactics (e.g. reconnaissance, resource_development) it never shows."""
        self.assertEqual(set(TACTIC_ORDER), VALID_MITRE_TACTICS)
        for tactic in TACTIC_ORDER:
            self.assertIn(tactic, TACTIC_DISPLAY, f"{tactic} has no display name")

    def test_non_attack_tactics_are_filtered_from_catalog_scalars(self):
        """Junk tactic labels carried by Sentinel conversions (e.g. 'malware,_component',
        'vulnerability') must never inflate the catalog's tactic count. Only the 14
        canonical ATT&CK enterprise tactics may appear in the aggregate scalars."""
        self.assertEqual(len(VALID_MITRE_TACTICS), 14)

        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            queries_dir = project_dir / "queries"
            apps_dir = queries_dir / "apps"
            hunting_dir = queries_dir / "hunting"
            apps_dir.mkdir(parents=True, exist_ok=True)
            hunting_dir.mkdir(parents=True, exist_ok=True)

            (queries_dir / "clean_detection.json").write_text(json.dumps({
                "title": "Clean Detection",
                "query": "'Log Source' = 'OCI Audit Logs'",
                "sigma_id": "sigma-clean-001",
                "level": "high",
                "logsource": {"product": "oci", "service": "audit"},
                "mitre_attack": {"tactics": ["execution"], "techniques": ["T1059"]},
            }))
            (queries_dir / "junk_tactic_detection.json").write_text(json.dumps({
                "title": "Sentinel-derived Junk Tactic",
                "query": "'Log Source' = 'OCI Audit Logs'",
                "sentinel_id": "sentinel-junk-001",
                "source_type": "microsoft_sentinel",
                "level": "medium",
                "logsource": {"product": "oci", "service": "audit"},
                "mitre_attack": {
                    "tactics": ["execution", "malware,_component", "vulnerability"],
                    "techniques": ["T1059"],
                },
            }))

            detections, app_queries, hunting = load_query_surfaces(queries_dir, apps_dir, hunting_dir)
            inventory = get_inventory_counts(project_dir, queries_dir, apps_dir, hunting_dir)
            catalog = generate_json_catalog(detections, app_queries, hunting, inventory=inventory)

            self.assertIn("execution", catalog["all_mitre_tactics"])
            self.assertNotIn("malware,_component", catalog["all_mitre_tactics"])
            self.assertNotIn("vulnerability", catalog["all_mitre_tactics"])
            self.assertNotIn("malware,_component", catalog["mitre_tactics"])
            self.assertTrue(set(catalog["all_mitre_tactics"]) <= VALID_MITRE_TACTICS)
            self.assertEqual(
                catalog["inventory"]["combined_mitre_tactics"],
                len(catalog["all_mitre_tactics"]),
            )

            # Per-rule tactic lists must also be free of non-ATT&CK labels so no
            # rule advertises a tactic that is absent from the aggregate scalars.
            for surface in ("rules", "sentinel_queries", "app_queries"):
                for entry in catalog.get(surface, []):
                    self.assertTrue(
                        set(entry.get("mitre_tactics", [])) <= VALID_MITRE_TACTICS,
                        f"{surface} entry {entry.get('title')!r} carries a non-ATT&CK tactic",
                    )


if __name__ == "__main__":
    unittest.main()
