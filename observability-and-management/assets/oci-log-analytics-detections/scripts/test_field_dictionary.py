#!/usr/bin/env python3
"""Tests for generated log source field dictionary artifacts."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from field_dictionary import (  # noqa: E402
    _load_query_payloads,
    build_query_field_coverage_report,
    build_field_dictionary,
    extract_query_fields,
    sanitize_example_value,
    validate_field_dictionary,
    validate_query_field_coverage,
)


class TestFieldDictionary(unittest.TestCase):
    """Validate parser/source field dictionary generation and gates."""

    def test_extract_query_fields_handles_quoted_oci_fields(self):
        fields = extract_query_fields(
            "'Log Source' = 'SOC Application Logs' and 'Trace ID' != null "
            "| stats count as Events by 'Service Name', 'Trace ID'"
        )

        self.assertIn("Log Source", fields)
        self.assertIn("Trace ID", fields)
        self.assertIn("Service Name", fields)
        self.assertNotIn("SOC Application Logs", fields)

    def test_build_field_dictionary_indexes_parser_fields_and_usage(self):
        dictionary = build_field_dictionary(
            parser_definitions=[
                {
                    "parser_name": "testParser",
                    "parser_display": "Test Parser",
                    "source_internal": "testSource",
                    "source_display": "SOC Test Logs",
                    "field_mappings": [
                        ("msg", "$.message", 1),
                        ("Trace ID", "$.trace_id", 2),
                    ],
                    "example": {"message": "hello", "trace_id": "trace_001"},
                }
            ],
            source_candidate_groups={"test_logs": ["SOC Test Logs"]},
            query_payloads=[
                (
                    "queries/apps/test.json",
                    {
                        "title": "Trace Pivot",
                        "query": "'Log Source' = 'SOC Test Logs' | stats count as Events by 'Trace ID'",
                    },
                )
            ],
            contracts={
                "test.jsonl": {
                    "required_fields": ["message", "trace_id"],
                    "minimum_events": 1,
                }
            },
        )

        fields = {field["display_name"]: field for field in dictionary["fields"]}
        self.assertIn("Trace ID", fields)
        self.assertEqual(fields["Trace ID"]["type"], "STRING")
        self.assertEqual(fields["Trace ID"]["example_values"], ["trace_001"])
        self.assertEqual(fields["Trace ID"]["queries_using_it"], ["queries/apps/test.json"])
        self.assertEqual(fields["Trace ID"]["source_candidate_groups"], ["test_logs"])

    def test_query_payload_loader_ignores_generated_support_artifacts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            queries_dir = Path(tmpdir)
            (queries_dir / "valid_query.json").write_text(
                json.dumps({
                    "title": "Valid Query",
                    "query": "'Log Source' = 'SOC Test Logs' | stats count by 'Trace ID'",
                }),
                encoding="utf-8",
            )
            (queries_dir / "sentinel_synthetic_plan.json").write_text(
                json.dumps({
                    "summary": {"synthetic_ready": 1},
                    "query": "'Missing Field' = 'not a saved search'",
                }),
                encoding="utf-8",
            )

            payloads = _load_query_payloads(queries_dir=queries_dir)

            self.assertEqual([path for path, _payload in payloads], ["valid_query.json"])

    def test_query_field_coverage_report_is_machine_readable(self):
        dictionary = {
            "fields": [{"display_name": "Trace ID"}],
            "approved_builtins": ["Log Source", "Count"],
        }
        payloads = [
            (
                "queries/good.json",
                {"query": "'Log Source' = 'SOC Test Logs' | stats count by 'Trace ID'"},
            ),
            (
                "queries/bad.json",
                {"query": "'Log Source' = 'SOC Test Logs' | stats count by 'Missing Field'"},
            ),
        ]

        report = build_query_field_coverage_report(dictionary, query_payloads=payloads)

        self.assertFalse(report["ok"])
        self.assertEqual(report["total_query_files"], 2)
        self.assertEqual(report["unknown_field_count"], 1)
        self.assertEqual(
            report["unknown_fields"],
            [{"query_file": "queries/bad.json", "field": "Missing Field"}],
        )

    def test_example_values_are_variable_safe(self):
        value = (
            "actor user@example.com from 198.51.100.44 touched "
            "ocid1.instance.oc1.iad.example via https://service.example.test/path"
        )

        self.assertEqual(
            sanitize_example_value(value),
            "actor <USER_EMAIL> from <IP_ADDRESS> touched "
            "<OCI_RESOURCE_OCID> via <URL>",
        )

    def test_validate_dictionary_blocks_reserved_original_log_content_mapping(self):
        dictionary = build_field_dictionary(
            parser_definitions=[
                {
                    "parser_name": "badParser",
                    "parser_display": "Bad Parser",
                    "source_internal": "badSource",
                    "source_display": "Bad Source",
                    "field_mappings": [("Original Log Content", "$.message", 1)],
                    "example": {"message": "bad"},
                }
            ],
            source_candidate_groups={},
            query_payloads=[],
            contracts={},
        )

        errors = validate_field_dictionary(dictionary)

        self.assertTrue(any("Original Log Content" in error for error in errors))

    def test_validate_query_field_coverage_reports_missing_field(self):
        dictionary = {
            "fields": [{"display_name": "Trace ID"}],
            "approved_builtins": ["Log Source", "Count"],
        }
        payload = {
            "title": "Missing Field",
            "query": "'Log Source' = 'SOC Test Logs' | stats count as Count by 'Missing Field'",
        }

        errors = validate_query_field_coverage("queries/test.json", payload, dictionary)

        self.assertEqual(errors, ["queries/test.json: unknown query field 'Missing Field'"])


if __name__ == "__main__":
    unittest.main()
