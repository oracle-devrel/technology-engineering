#!/usr/bin/env python3
"""Tests for SIEM discovery and migration report artifacts."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.siem_discovery_report import (
    azure_inventory,
    build_migration_plan,
    extract_externaldata_dependencies,
    migration_report,
    redact_sensitive_values,
    sentinel_inventory,
    validate_payload_against_schema,
)
from scripts.kql._facade_impl import extract_source_tables


class TestSiemDiscoveryReport(unittest.TestCase):
    def test_sentinel_inventory_envelope_and_coverage(self):
        candidates = [
            {
                "sentinel_id": "rule-1",
                "title": "Suspicious sign-in",
                "kind": "analytics_rule",
                "query": "SigninLogs | where UserPrincipalName == 'alice@example.com'",
                "severity": "high",
                "query_frequency": "PT5M",
                "query_period": "PT1H",
                "required_data_connectors": [{"connectorId": "AzureActiveDirectory"}],
                "source_path": "Detections/Signin/rule.yaml",
                "hit_counts_by_lookback": {"24h": 12},
                "stored_log_volume_bytes": 2_000_000,
                "dashboard_references": ["Workbook A"],
            }
        ]

        inventory = sentinel_inventory(candidates, {"name": "test"})

        self.assertEqual(inventory["version"], "1.0")
        self.assertEqual(inventory["summary"]["content_count"], 1)
        item = inventory["items"][0]
        self.assertEqual(item["content_id"], "rule-1")
        self.assertEqual(item["source_tables"], ["SigninLogs"])
        self.assertIn("Azure Entra ID Sign-in Logs", item["mapped_oci_sources"])
        self.assertEqual(item["missing_tables"], [])
        self.assertEqual(item["hit_counts_by_lookback"], {"24h": 12})

    def test_externaldata_feed_dependencies_are_discovered(self):
        query = (
            "let knownUserAgentsIndicators = materialize(externaldata(UserAgent:string, Category:string)\n"
            "  [ @\"https://raw.githubusercontent.com/Azure/Azure-Sentinel/master/Sample%20Data/Feeds/UnusualUserAgents.csv\" ]\n"
            "  with(format=\"csv\", ignoreFirstRecord=True));\n"
            "_Im_WebSession | where HttpUserAgent has_any (knownUserAgentsIndicators)"
        )

        dependencies = extract_externaldata_dependencies(query)

        self.assertEqual(len(dependencies), 1)
        self.assertEqual(dependencies[0]["kind"], "externaldata")
        self.assertEqual(dependencies[0]["name"], "knownUserAgentsIndicators")
        self.assertEqual(dependencies[0]["format"], "csv")
        self.assertEqual(dependencies[0]["columns"], [
            {"name": "UserAgent", "type": "string"},
            {"name": "Category", "type": "string"},
        ])
        self.assertEqual(dependencies[0]["options"]["ignoreFirstRecord"], "True")
        self.assertIn("UnusualUserAgents.csv", dependencies[0]["url"])

        h_literal = extract_externaldata_dependencies(
            "let TorNodes = (externaldata (TorIP:string) "
            "[h@'https://firewalliplists.example.test/kusto-tor-exit.csv.zip'] "
            "with (ignoreFirstRecord=true)); AWSCloudTrail"
        )
        self.assertEqual(h_literal[0]["url"], "https://firewalliplists.example.test/kusto-tor-exit.csv.zip")
        self.assertEqual(h_literal[0]["name"], "TorNodes")

        inventory = sentinel_inventory([{
            "sentinel_id": "feed-rule",
            "title": "Feed backed rule",
            "kind": "analytics_rule",
            "query": query,
            "severity": "medium",
            "source_path": "Detections/feed.yaml",
        }], {"name": "test"})
        item = inventory["items"][0]

        self.assertEqual(inventory["summary"]["feed_dependency_count"], 1)
        self.assertEqual(item["feed_dependencies"], dependencies)

        plan = build_migration_plan(inventory, migration_report(inventory))
        self.assertEqual(plan["items"][0]["feed_dependencies"], dependencies)
        self.assertEqual(plan["items"][0]["next_validation"], "feed_staging")
        self.assertEqual(migration_report(inventory)["summary"]["feed_dependency_count"], 1)

    def test_migration_report_classifies_table_and_field_blockers(self):
        inventory = {
            "version": "1.0",
            "generated_at": "2026-05-28T00:00:00Z",
            "platform": "microsoft_sentinel",
            "summary": {},
            "items": [
                {
                    "content_id": "blocked",
                    "title": "Blocked",
                    "enabled": True,
                    "severity": "medium",
                    "source_tables": ["UnknownTable"],
                    "field_usage": ["UnknownField"],
                    "mapped_oci_sources": [],
                    "missing_tables": ["UnknownTable"],
                    "missing_fields": ["UnknownField"],
                    "hit_counts_by_lookback": {},
                    "stored_log_volume_bytes": 0,
                    "dashboard_references": [],
                    "migration_status": "blocked",
                    "blockers": [
                        {"type": "table_mapping", "detail": "UnknownTable"},
                        {"type": "field_mapping", "detail": "UnknownField"},
                    ],
                }
            ],
        }

        report = migration_report(inventory)

        self.assertEqual(report["summary"]["blocked_count"], 1)
        self.assertEqual(report["summary"]["blocker_counts"]["table_mapping"], 1)
        self.assertEqual(report["items"][0]["blocker_type"], "table_mapping")

    def test_redaction_removes_tenant_request_ocid_and_ip_values(self):
        request_id = "opc" + "-request-id: " + "abcdef1234567890"
        ocid = "ocid1" + ".instance.oc1..aaaa"
        ip_address = ".".join(["144", "24", "1", "2"])
        tenant = "-".join(["00000000", "1111", "2222", "3333", "444444444444"])
        payload = {
            "message": f"{request_id} {ocid} {ip_address} https://login.microsoftonline.com/{tenant}",
        }

        redacted = redact_sensitive_values(payload)

        text = json.dumps(redacted)
        self.assertNotIn("ocid1.instance", text)
        self.assertNotIn("144.24.1.2", text)
        self.assertNotIn("abcdef1234567890", text)
        self.assertNotIn("00000000-1111-2222-3333-444444444444", text)

    def test_azure_offline_inventory_uses_same_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "azure.json"
            path.write_text(json.dumps({
                "items": [
                    {
                        "id": "az-1",
                        "name": "Azure rule",
                        "kql": "AzureActivity | where OperationName == 'Delete'",
                        "enabled": False,
                    }
                ]
            }), encoding="utf-8")

            inventory = azure_inventory(path)

        self.assertEqual(inventory["platform"], "azure_log_analytics")
        self.assertEqual(inventory["items"][0]["content_id"], "az-1")
        self.assertEqual(inventory["items"][0]["enabled"], False)

    def test_schema_validation_reports_missing_required_fields(self):
        errors = validate_payload_against_schema({"version": "1.0"}, {
            "type": "object",
            "required": ["version", "items"],
            "properties": {
                "version": {"type": "string"},
                "items": {"type": "array"},
            },
        })

        self.assertEqual(errors, ["$: missing required field items"])

    def test_migration_plan_preserves_duplicate_content_id_blockers(self):
        inventory = {
            "items": [
                {
                    "content_id": "duplicate",
                    "title": "Ready",
                    "kind": "analytics_rule",
                    "enabled": True,
                    "severity": "medium",
                    "source_tables": ["SigninLogs"],
                    "mapped_oci_sources": ["Azure Entra ID Sign-in Logs"],
                    "migration_status": "ready_for_local_validation",
                    "blockers": [],
                },
                {
                    "content_id": "duplicate",
                    "title": "Blocked",
                    "kind": "analytics_rule",
                    "enabled": True,
                    "severity": "medium",
                    "source_tables": ["UnknownTable"],
                    "mapped_oci_sources": [],
                    "migration_status": "blocked",
                    "blockers": [{"type": "table_mapping", "detail": "UnknownTable"}],
                },
            ],
        }
        report = {
            "report_path": "docs/health/siem-migration-test.json",
            "items": inventory["items"],
        }

        plan = build_migration_plan(inventory, report)

        self.assertEqual(plan["summary"]["planned_count"], 2)
        self.assertEqual(plan["summary"]["ready_for_local_validation_count"], 1)
        self.assertEqual(plan["summary"]["blocked_count"], 1)

    def test_source_table_extraction_ignores_non_source_preamble(self):
        self.assertEqual(
            extract_source_tables("""
            // Sentinel note
            let lookback = 1d;
            _Im_NetworkSession(eventresult="Failure", starttime=ago(lookback))
            | where DstPortNumber == 3389
            """),
            ["_Im_NetworkSession"],
        )
        self.assertEqual(extract_source_tables("# Dataverse exported comment"), [])
        self.assertEqual(extract_source_tables("declare query_parameters(test:string);"), [])
        self.assertEqual(
            extract_source_tables("""
            let threshold = 1;
            union isfuzzy=true(
              AZFWApplicationRule | where Action == "Deny"),
              (AzureDiagnostics | where OperationName == "AzureFirewallApplicationRuleLog")
            | project Action
            """),
            ["AZFWApplicationRule", "AzureDiagnostics"],
        )
        self.assertEqual(
            extract_source_tables("""
            let UserAgentList = 'tool';
            (union isfuzzy=true
              (OfficeActivity | where UserAgent has UserAgentList),
              (CommonSecurityLog | where RequestClientApplication has UserAgentList))
            | project TimeGenerated
            """),
            ["OfficeActivity", "CommonSecurityLog"],
        )


if __name__ == "__main__":
    unittest.main()
