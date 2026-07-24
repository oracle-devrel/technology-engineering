#!/usr/bin/env python3
"""Prevent application/browser queries from drifting back to unsupported fields."""

import json
import os
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oci_config import APPS_DIR, PROJECT_DIR
from field_dictionary import extract_query_fields


LEGACY_QUERY_TOKENS = [
    "service.name",
    "security.attack.",
    "security.source_ip",
    "security.username",
    "security.waf.score",
    "http.url.path",
    "http.response_time_ms",
    "http.status_code",
    "performance.slow_request",
    "orders.sync.",
    "trace_id",
    "db.target",
    "HTTP URL",
    " is not null",
    "avg('Response Time Ms')",
    "max('Response Time Ms')",
    "sum('Orders Sync",
]


class TestAppQueryContract(unittest.TestCase):
    """Validate the public app/browser query contract."""

    def test_queries_use_supported_soc_application_schema(self):
        query_files = sorted(Path(APPS_DIR).glob("*.json"))
        query_files.append(Path(PROJECT_DIR) / "queries" / "hunting" / "browser_attack_frequency_analysis.json")

        self.assertGreater(len(query_files), 0)

        for path in query_files:
            with path.open() as f:
                payload = json.load(f)
            query = payload["query"]

            self.assertIn("SOC Application Logs", query, path.name)
            self.assertNotIn("enterprise-crm-portal'", query, path.name)
            self.assertNotIn("octo-drone-shop'", query, path.name)

            for token in LEGACY_QUERY_TOKENS:
                self.assertNotIn(token, query, f"{path.name} still uses legacy token: {token}")

            if "| stats " in query and " by " in query:
                stats_section = query.split("| stats ", 1)[1].split("|", 1)[0]
                if " by " in stats_section:
                    by_clause = stats_section.split(" by ", 1)[1]
                    group_fields = [field.strip() for field in by_clause.split(",") if field.strip()]
                    self.assertLessEqual(
                        len(group_fields),
                        4,
                        f"{path.name} exceeds OCI Log Analytics four-field STATS limit",
                    )

    def test_waf_only_queries_use_waf_parser_backed_fields(self):
        dictionary = _load_field_dictionary()
        source_fields = _fields_for_source(dictionary, "SOC WAF Security Logs")
        approved = set(dictionary.get("approved_builtins", []))
        query_files = sorted(
            list((Path(PROJECT_DIR) / "queries").glob("waf_*.json"))
            + list((Path(PROJECT_DIR) / "queries" / "hunting").glob("waf_*.json"))
        )

        self.assertGreater(len(query_files), 0)

        for path in query_files:
            with path.open() as f:
                payload = json.load(f)
            query = payload["query"]
            fields = set(extract_query_fields(query))
            unsupported = sorted(fields - source_fields - approved)

            self.assertIn("SOC WAF Security Logs", query, path.name)
            self.assertNotIn("SOC Application Logs", query, path.name)
            self.assertEqual(unsupported, [], f"{path.name} has non-WAF-backed fields: {unsupported}")

    def test_app_waf_correlation_queries_use_declared_source_fields(self):
        dictionary = _load_field_dictionary()
        approved = set(dictionary.get("approved_builtins", []))
        sources_by_field = _field_sources_by_name(dictionary)
        known_sources = {
            "SOC Application Logs",
            "SOC WAF Security Logs",
            "SOC Web Application Logs",
        }
        query_files = [
            Path(APPS_DIR) / "apm_attack_to_waf_correlation.json",
            Path(APPS_DIR) / "apm_trace_correlation_link.json",
            Path(APPS_DIR) / "app_waf_signal_correlation.json",
        ]

        for path in query_files:
            with path.open() as f:
                payload = json.load(f)
            query = payload["query"]
            declared_sources = {source for source in known_sources if source in query}
            fields = set(extract_query_fields(query))

            self.assertIn("SOC Application Logs", query, path.name)
            self.assertGreater(len(declared_sources), 0, path.name)
            for field in sorted(fields - approved):
                self.assertTrue(
                    sources_by_field.get(field, set()) & declared_sources,
                    f"{path.name} field {field!r} is not backed by declared sources {sorted(declared_sources)}",
                )

    def test_octo_dashboard_visualization_fields_are_query_outputs(self):
        """Keep dashboard metadata aligned with the fields emitted by OCTO queries."""
        option_fields = {"valueField", "highlightField", "xField", "yField", "seriesField"}

        for path in sorted(Path(APPS_DIR).glob("apm_octo_*.json")):
            with path.open() as f:
                payload = json.load(f)

            output_fields = _infer_dashboard_output_fields(payload["query"])
            dashboard = payload.get("dashboard", {})
            visualization_options = dashboard.get("visualizationOptions", {})

            for option_name in option_fields:
                field_name = visualization_options.get(option_name)
                if field_name:
                    self.assertIn(
                        field_name,
                        output_fields,
                        f"{path.name} dashboard {option_name}={field_name!r} is not emitted by the query",
                    )

            tile_layout = visualization_options.get("tileLayoutXml", "")
            for field_name in re.findall(r'<tile field="([^"]+)"', tile_layout):
                self.assertIn(
                    field_name,
                    output_fields,
                    f"{path.name} tile field {field_name!r} is not emitted by the query",
                )
            for field_name in re.findall(r'<chart-value field="([^"]+)"', tile_layout):
                self.assertIn(
                    field_name,
                    output_fields,
                    f"{path.name} chart value field {field_name!r} is not emitted by the query",
                )
            for field_name in re.findall(r'series-field="([^"]+)"', tile_layout):
                self.assertIn(
                    field_name,
                    output_fields,
                    f"{path.name} chart series field {field_name!r} is not emitted by the query",
                )
            for field_name in re.findall(r'<param field="([^"]+)"', tile_layout):
                self.assertIn(
                    field_name,
                    output_fields,
                    f"{path.name} Ask AI parameter field {field_name!r} is not emitted by the query",
                )


def _strip_field_name(value):
    return value.strip().strip("'\"")


def _split_fields(value):
    return [_strip_field_name(field) for field in value.split(",") if field.strip()]


def _infer_dashboard_output_fields(query):
    """Infer stable result fields from the query shapes used by app dashboards."""
    output_fields = set()

    for command in query.split("|"):
        command = command.strip()
        command_lower = command.lower()

        if command_lower.startswith("fields "):
            output_fields.update(_split_fields(command[7:]))
            continue

        if command_lower.startswith("stats ") or command_lower.startswith("timestats "):
            if command_lower.startswith("timestats "):
                output_fields.add("Time")

            alias_pattern = r"\bas\s+('([^']+)'|\"([^\"]+)\"|[A-Za-z][A-Za-z0-9_ %.-]*?)(?=,|\s+by\b|$)"
            for alias in re.findall(alias_pattern, command):
                output_fields.add(_strip_field_name(alias[1] or alias[2] or alias[0]))

            by_match = re.search(r"\sby\s(.+)$", command, flags=re.IGNORECASE)
            if by_match:
                output_fields.update(_split_fields(by_match.group(1)))
            continue

        if command_lower.startswith("link "):
            quoted_fields = re.findall(r"'([^']+)'", command)
            output_fields.update(quoted_fields)
            output_fields.add("Count")
            continue

        if command_lower.startswith("eventstats "):
            alias_pattern = r"\bas\s+('([^']+)'|\"([^\"]+)\"|[A-Za-z][A-Za-z0-9_ %.-]*?)(?=,|\s+by\b|$)"
            for alias in re.findall(alias_pattern, command):
                output_fields.add(_strip_field_name(alias[1] or alias[2] or alias[0]))

    return output_fields


def _load_field_dictionary():
    with (Path(PROJECT_DIR) / "queries" / "log_source_field_dictionary.json").open() as f:
        return json.load(f)


def _field_sources_by_name(dictionary):
    return {
        field.get("display_name", ""): {
            source.get("source_display", "")
            for source in field.get("sources", [])
            if source.get("source_display")
        }
        for field in dictionary.get("fields", [])
    }


def _fields_for_source(dictionary, source_display):
    return {
        field
        for field, sources in _field_sources_by_name(dictionary).items()
        if source_display in sources
    }


if __name__ == "__main__":
    unittest.main()
