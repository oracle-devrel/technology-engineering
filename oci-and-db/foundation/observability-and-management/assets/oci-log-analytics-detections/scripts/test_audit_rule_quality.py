#!/usr/bin/env python3
"""Unit tests for the rule quality audit helpers."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_rule_quality import (
    check_missing_falsepositives,
    check_missing_mitre_tags,
    check_missing_stable_id,
    check_missing_version,
    load_all_queries,
    load_all_rules,
)


class TestAuditRuleQuality(unittest.TestCase):
    """Validate quality-audit loading behavior."""

    @staticmethod
    def complete_rule(**overrides):
        rule = {
            "title": "Complete Rule",
            "id": "11111111-1111-1111-1111-111111111111",
            "version": 1,
            "tags": ["attack.execution", "attack.t1059"],
            "falsepositives": ["Authorized administration"],
        }
        rule.update(overrides)
        return rule

    def test_load_all_rules_reports_invalid_yaml(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir)
            (rules_dir / "good.yaml").write_text(
                "title: Good Rule\n"
                "id: good-001\n"
                "logsource:\n"
                "  product: oci\n"
                "  service: audit\n"
                "detection:\n"
                "  selection:\n"
                "    event_type: test\n"
                "  condition: selection\n"
            )
            (rules_dir / "bad.yaml").write_text("title: Broken Rule\nauthor: Team: Example\n")

            rules, errors = load_all_rules(rules_dir)

            self.assertEqual(len(rules), 1)
            self.assertEqual(len(errors), 1)
            self.assertIn("Invalid YAML", errors[0]["issue"])
            self.assertEqual(errors[0]["severity"], "critical")

    def test_load_all_queries_walks_subdirs_and_filters_curated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            queries_dir = Path(tmpdir)
            apps_dir = queries_dir / "apps"
            apps_dir.mkdir(parents=True, exist_ok=True)

            (queries_dir / "base.json").write_text(json.dumps({
                "title": "Base Rule",
                "query": "'Log Source' = 'OCI Audit Logs'",
                "sigma_id": "base-001",
            }))
            (apps_dir / "browser.json").write_text(json.dumps({
                "title": "Browser Rule",
                "query": "'Log Source' = 'SOC Application Logs'",
                "sigma_id": "browser-001",
            }))
            (apps_dir / "curated.json").write_text(json.dumps({
                "title": "Curated App Query",
                "query": "'Log Source' = 'SOC Application Logs'",
            }))

            queries = load_all_queries(queries_dir)
            files = {q["_file"] for q in queries}

            self.assertEqual(len(queries), 2)
            self.assertIn("base.json", files)
            self.assertIn("apps/browser.json", files)
            self.assertNotIn("apps/curated.json", files)

    def test_required_metadata_checks_flag_missing_fields(self):
        missing_id = self.complete_rule(id="")
        id_issues = check_missing_stable_id([missing_id])
        self.assertEqual(len(id_issues), 1)
        self.assertIn("Missing stable ID", id_issues[0]["issue"])
        self.assertIn(id_issues[0]["severity"], {"critical", "high", "medium", "low"})

        version_issues = check_missing_version([self.complete_rule(version=None)])
        self.assertEqual(len(version_issues), 1)
        self.assertIn("Missing version field", version_issues[0]["issue"])

        falsepositive_issues = check_missing_falsepositives([self.complete_rule(falsepositives=[])])
        self.assertEqual(len(falsepositive_issues), 1)
        self.assertIn("Missing falsepositives field", falsepositive_issues[0]["issue"])

        mitre_issues = check_missing_mitre_tags([self.complete_rule(tags=["attack.execution"])])
        self.assertEqual(len(mitre_issues), 1)
        self.assertIn("No MITRE ATT&CK technique tags", mitre_issues[0]["issue"])

    def test_required_metadata_checks_accept_complete_rule(self):
        rule = self.complete_rule()

        self.assertEqual(check_missing_stable_id([rule]), [])
        self.assertEqual(check_missing_version([rule]), [])
        self.assertEqual(check_missing_falsepositives([rule]), [])
        self.assertEqual(check_missing_mitre_tags([rule]), [])


if __name__ == "__main__":
    unittest.main()
