#!/usr/bin/env python3
"""Smoke tests for dashboard wiring and visualization metadata."""

import json
import io
import os
import re
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deploy_dashboard import (
    DASHBOARDS,
    SUPPORTED_VISUALIZATION_TYPES,
    build_dashboard_inventory,
    build_dashboard_json,
    build_saved_search_json,
    load_sentinel_dashboard_groups,
    resolve_widget_ui_config,
    select_dashboards,
    validate_dashboard_inventory,
    validate_inventory_queries_in_oci,
)
from oci_config import QUERIES_DIR


UNSUPPORTED_DASHBOARD_QUERY_PATTERNS = (
    "regexextract(",
    "countif(",
    "case(",
    " REGEX MATCH ",
    "TicketEncryptionType",
    "PrivilegeList",
    "Properties like",
    "'Request Action Type'",
    "'Target Server Name'",
)


class TestDashboardContract(unittest.TestCase):
    """Validate dashboard widgets and saved-search visualization metadata."""

    def test_dashboard_widgets_reference_existing_query_files(self):
        for dashboard_name, config in DASHBOARDS.items():
            self.assertGreater(len(config["widgets"]), 0, dashboard_name)
            for widget in config["widgets"]:
                query_path = Path(QUERIES_DIR) / widget["query_file"]
                self.assertTrue(query_path.exists(), f"{dashboard_name}: missing {widget['query_file']}")

    def test_dashboards_stay_under_oci_widget_limit(self):
        for dashboard_name, config in DASHBOARDS.items():
            self.assertLessEqual(
                len(config["widgets"]),
                30,
                f"{dashboard_name} has too many widgets for a focused SOC dashboard",
            )

    def test_query_visualization_metadata_is_supported(self):
        for config in DASHBOARDS.values():
            for widget in config["widgets"]:
                query_path = Path(QUERIES_DIR) / widget["query_file"]
                with query_path.open() as f:
                    payload = json.load(f)

                dashboard_meta = payload.get("dashboard", {})
                visualization_type = dashboard_meta.get("visualizationType")
                if visualization_type:
                    self.assertIn(visualization_type, SUPPORTED_VISUALIZATION_TYPES, query_path.name)

                ask_ai_prompts = dashboard_meta.get("ask_ai_prompts", [])
                self.assertIsInstance(ask_ai_prompts, list, query_path.name)
                for prompt in ask_ai_prompts:
                    self.assertIsInstance(prompt, str, query_path.name)
                    self.assertTrue(prompt.strip(), query_path.name)

    def test_dashboard_queries_avoid_unsupported_live_validation_patterns(self):
        for dashboard_name, config in DASHBOARDS.items():
            for widget in config["widgets"]:
                query_path = Path(QUERIES_DIR) / widget["query_file"]
                with query_path.open() as f:
                    payload = json.load(f)

                query = payload["query"]
                for pattern in UNSUPPORTED_DASHBOARD_QUERY_PATTERNS:
                    self.assertNotIn(
                        pattern,
                        query,
                        f"{dashboard_name}: {widget['query_file']} contains {pattern}",
                    )

    def test_resolve_widget_ui_config_uses_query_dashboard_metadata(self):
        widget = {"title": "Geo map"}
        query_info = {
            "query": "'Log Source' = 'SOC Multicloud Health Logs' | stats count",
            "dashboard": {
                "visualizationType": "map",
                "ask_ai_prompts": ["Summarize the current cloud health posture."],
                "timeSelection": {"timePeriod": "l24h"},
            },
        }

        ui_config = resolve_widget_ui_config(widget, query_info)

        self.assertEqual(ui_config["visualizationType"], "map")
        self.assertEqual(ui_config["timeSelection"], {"timePeriod": "l24h"})
        self.assertEqual(ui_config["queryString"], query_info["query"])

    def test_resolve_widget_ui_config_defaults_to_demo_ready_time_window(self):
        widget = {"title": "Default time widget"}
        query_info = {"query": "'Log Source' = 'SOC Windows Sysmon Logs' | stats count"}

        ui_config = resolve_widget_ui_config(widget, query_info)

        self.assertEqual(ui_config["timeSelection"], {"timePeriod": "l21d"})

    def test_build_saved_search_json_defaults_to_demo_ready_time_window(self):
        saved_search = build_saved_search_json(
            search_id="default-time",
            title="Default Time",
            query="'Log Source' = 'SOC Windows Sysmon Logs' | stats count",
        )

        self.assertEqual(saved_search["uiConfig"]["timeSelection"], {"timePeriod": "l21d"})

    def test_build_dashboard_json_time_parameter_matches_widget_default(self):
        widget = {"title": "Default Time", "query_file": "default_time.json"}
        query_info = {"query": "'Log Source' = 'SOC Windows Sysmon Logs' | stats count"}

        dashboard = build_dashboard_json(
            dashboard_id="soc-default-time",
            name="Default Time Dashboard",
            description="test",
            widgets=[widget],
            widget_queries=[query_info],
        )

        time_parameter = next(
            parameter for parameter in dashboard["parametersConfig"]
            if parameter["paramName"] == "time"
        )
        saved_search = dashboard["savedSearches"][0]
        self.assertEqual(time_parameter["defaultValue"], "l21d")
        self.assertEqual(saved_search["uiConfig"]["timeSelection"], {"timePeriod": "l21d"})

    def test_build_dashboard_json_saved_search_ids_unique_per_deploy(self):
        # Saved-search IDs must carry the dashboard's per-deploy suffix so OCI's
        # soft-delete cannot resurrect a stale same-named saved search after a
        # --cleanup run. Two deploys (different dashboard_id) must yield different
        # saved-search IDs, and every tile reference must match a saved search.
        widget = {"title": "Reverse Shell", "query_file": "linux_reverse_shell_detected.json"}
        query_info = {"query": "'Log Source' = 'SOC Linux Syslog Logs' | stats count"}

        first = build_dashboard_json(
            dashboard_id="soc-overview-1111111111",
            name="SOC Overview", description="test",
            widgets=[widget], widget_queries=[query_info],
        )
        second = build_dashboard_json(
            dashboard_id="soc-overview-2222222222",
            name="SOC Overview", description="test",
            widgets=[widget], widget_queries=[query_info],
        )

        first_id = first["savedSearches"][0]["id"]
        second_id = second["savedSearches"][0]["id"]
        self.assertTrue(first_id.endswith("-1111111111"), first_id)
        self.assertTrue(second_id.endswith("-2222222222"), second_id)
        self.assertNotEqual(first_id, second_id)
        # Tile reference stays consistent with the embedded saved search.
        self.assertEqual(first["tiles"][0]["savedSearchId"], first_id)
        self.assertEqual(second["tiles"][0]["savedSearchId"], second_id)

    def test_build_dashboard_json_layout_prevents_tile_overlap(self):
        for dashboard_name, config in DASHBOARDS.items():
            widget_queries = []
            for widget in config["widgets"]:
                with (Path(QUERIES_DIR) / widget["query_file"]).open() as f:
                    widget_queries.append(json.load(f))

            dashboard = build_dashboard_json(
                dashboard_id=f"layout-{dashboard_name}",
                name=dashboard_name,
                description=config["description"],
                widgets=config["widgets"],
                widget_queries=widget_queries,
            )

            tiles = dashboard["tiles"]
            for left_index, left in enumerate(tiles):
                for right in tiles[left_index + 1:]:
                    separated = (
                        left["column"] + left["width"] <= right["column"]
                        or right["column"] + right["width"] <= left["column"]
                        or left["row"] + left["height"] <= right["row"]
                        or right["row"] + right["height"] <= left["row"]
                    )
                    self.assertTrue(
                        separated,
                        f"{dashboard_name}: {left['displayName']} overlaps {right['displayName']}",
                    )

    def test_table_widgets_get_full_width_layout(self):
        widgets = [
            {"title": "Wide Table 1", "query_file": "wide_table_1.json"},
            {"title": "Wide Table 2", "query_file": "wide_table_2.json"},
        ]
        query_info = {
            "query": "'Log Source' = 'SOC Application Logs' | stats count by 'Trace ID', 'Span Name'",
            "dashboard": {"visualizationType": "table"},
        }

        dashboard = build_dashboard_json(
            dashboard_id="wide-table-layout",
            name="Wide Table Layout",
            description="test",
            widgets=widgets,
            widget_queries=[query_info, query_info],
        )

        first, second = dashboard["tiles"]
        self.assertEqual(first["width"], 12)
        self.assertEqual(second["width"], 12)
        self.assertGreaterEqual(second["row"], first["row"] + first["height"])

    def test_build_dashboard_json_promotes_ask_ai_prompts_to_tags(self):
        widget = {"title": "Geo map", "query_file": "hunting/multicloud_geo_health_regional_map.json"}
        query_info = {
            "query": "'Log Source' = 'SOC Multicloud Health Logs' | stats count",
            "dashboard": {
                "visualizationType": "map",
                "ask_ai_prompts": ["Summarize the health posture."],
            },
            "tags": ["operations.health"],
        }

        dashboard = build_dashboard_json(
            dashboard_id="soc-test",
            name="Test Dashboard",
            description="test",
            widgets=[widget],
            widget_queries=[query_info],
        )

        saved_search = dashboard["savedSearches"][0]
        self.assertEqual(saved_search["uiConfig"]["visualizationType"], "map")
        self.assertIn("ask_ai_prompts", saved_search["freeformTags"])

    def test_select_dashboards_filters_by_display_name(self):
        selected = select_dashboards(["C2 & Beaconing Detection"])

        self.assertEqual(list(selected), ["C2 & Beaconing Detection"])
        self.assertEqual(len(selected["C2 & Beaconing Detection"]["widgets"]), 10)

    def test_dashboard_inventory_exports_query_metadata(self):
        inventory = build_dashboard_inventory(generated_at="2026-04-28T00:00:00+00:00")

        self.assertEqual(inventory["summary"]["total_dashboards"], len(DASHBOARDS))
        self.assertEqual(
            inventory["summary"]["total_widgets"],
            sum(len(config["widgets"]) for config in DASHBOARDS.values()),
        )
        self.assertIn("visualization_types", inventory["summary"])

        browser_dashboard = next(
            dashboard for dashboard in inventory["dashboards"]
            if dashboard["name"] == "SOC: Browser Attack Detection Dashboard"
        )
        total_attacks = next(
            widget for widget in browser_dashboard["widgets"]
            if widget["query_file"] == "apps/apm_total_attacks_kpi.json"
        )

        self.assertEqual(total_attacks["query_title"], "APM: Total Browser Attacks (24h)")
        self.assertEqual(total_attacks["visualization_type"], "tile")
        self.assertEqual(total_attacks["level"], "informational")
        self.assertIn("apm", total_attacks["tags"])

    def test_web_to_cloud_dashboard_covers_investigation_drilldown_widgets(self):
        dashboard = DASHBOARDS["SOC: Web-to-Cloud Threat Hunting Dashboard"]
        expected_query_files = {
            "hunting/web_to_cloud_attack_timeline.json",
            "hunting/web_to_cloud_entry_point.json",
            "hunting/web_to_cloud_compromised_machines.json",
            "hunting/web_to_cloud_compromised_identity.json",
            "hunting/web_to_cloud_vcn_egress.json",
            "hunting/web_to_cloud_firewall_c2.json",
            "hunting/web_to_cloud_cloud_abuse.json",
            "hunting/web_to_cloud_exfiltration.json",
            "hunting/web_to_cloud_attack_path_link.json",
            "hunting/web_to_cloud_mitre_sunburst.json",
        }
        actual_query_files = {widget["query_file"] for widget in dashboard["widgets"]}

        self.assertEqual(expected_query_files, actual_query_files)
        self.assertIn("entry point", dashboard["description"].lower())
        self.assertIn("exfiltration", dashboard["description"].lower())

        visualization_types = {}
        for query_file in expected_query_files:
            query_path = Path(QUERIES_DIR) / query_file
            with query_path.open() as f:
                payload = json.load(f)
            visualization_types[query_file] = payload.get("dashboard", {}).get("visualizationType")
            self.assertTrue(payload.get("dashboard", {}).get("ask_ai_prompts"), query_file)

        self.assertEqual(visualization_types["hunting/web_to_cloud_attack_path_link.json"], "link")
        # MITRE rollup renders as summary_table: a stats query under a sunburst viz
        # triggers OCI's records-companion "| fields Time" append and errors at render.
        self.assertEqual(visualization_types["hunting/web_to_cloud_mitre_sunburst.json"], "summary_table")
        self.assertIn("summary_table", set(visualization_types.values()))

    def test_c2_dashboard_covers_legacy_widgets_with_drilldowns(self):
        dashboard = DASHBOARDS["C2 & Beaconing Detection"]
        expected_query_files = {
            "hunting/c2_top_dns_domains.json",
            "hunting/c2_beacon_activity_timeline.json",
            "hunting/c2_dns_beacon_queries_kpi.json",
            "hunting/c2_destination_ips.json",
            "hunting/c2_communication_topology.json",
            "hunting/c2_dns_beacon_sources.json",
            "hunting/c2_unique_domains_kpi.json",
            "hunting/c2_flow_connections_kpi.json",
            "hunting/c2_https_beaconing.json",
            "hunting/c2_affected_hosts_kpi.json",
        }
        actual_query_files = {widget["query_file"] for widget in dashboard["widgets"]}

        self.assertEqual(expected_query_files, actual_query_files)
        self.assertIn("command-and-control", dashboard["description"].lower())

        visualization_types = {}
        for query_file in expected_query_files:
            query_path = Path(QUERIES_DIR) / query_file
            with query_path.open() as f:
                payload = json.load(f)
            visualization_types[query_file] = payload.get("dashboard", {}).get("visualizationType")
            self.assertEqual(payload.get("dashboard", {}).get("timeSelection"), {"timePeriod": "l21d"})
            self.assertTrue(payload.get("dashboard", {}).get("ask_ai_prompts"), query_file)

        self.assertEqual(visualization_types["hunting/c2_communication_topology.json"], "link")
        self.assertEqual(visualization_types["hunting/c2_beacon_activity_timeline.json"], "line")
        self.assertEqual(visualization_types["hunting/c2_dns_beacon_queries_kpi.json"], "tile")
        self.assertIn("summary_table", set(visualization_types.values()))

    def test_octo_apm_dashboard_covers_logs_spans_and_metrics(self):
        dashboard = DASHBOARDS["OCI-DEMO: Octo APM Demo Dashboard"]
        expected_query_files = {
            "apps/apm_octo_red_metrics.json",
            "apps/apm_octo_request_timeline.json",
            "apps/apm_octo_span_latency_hotspots.json",
            "apps/apm_octo_trace_logs_correlation.json",
            "apps/apm_octo_trace_investigation_tiles.json",
            "apps/apm_octo_span_link.json",
            "apps/apm_octo_error_logs.json",
            "apps/apm_octo_metric_samples.json",
            "apps/apm_octo_db_spans.json",
            "apps/apm_octo_java_sidecar_errors.json",
            "apps/apm_octo_api_gateway_edge.json",
            "apps/apm_octo_attack_timeline.json",
            "apps/apm_octo_attack_path_link.json",
            "apps/apm_octo_attack_trace_correlation.json",
            "apps/apm_octo_payment_threats.json",
            "apps/apm_octo_osquery_findings.json",
            "apps/apm_octo_compromised_vm_pivots.json",
        }
        actual_query_files = {widget["query_file"] for widget in dashboard["widgets"]}
        widgets_by_query_file = {widget["query_file"]: widget for widget in dashboard["widgets"]}

        self.assertEqual(expected_query_files, actual_query_files)
        self.assertIn("octo-apm-demo", dashboard["description"])

        visualization_types = set()
        for query_file in expected_query_files:
            query_path = Path(QUERIES_DIR) / query_file
            with query_path.open() as f:
                payload = json.load(f)

            query = payload["query"]
            visualization_types.add(payload.get("dashboard", {}).get("visualizationType"))
            self.assertIn("'Log Source' = 'SOC Application Logs'", query)
            self.assertIn("'Service Namespace' = 'octo'", query)
            self.assertTrue(payload.get("dashboard", {}).get("ask_ai_prompts"), query_file)
            self.assertEqual(
                resolve_widget_ui_config(widgets_by_query_file[query_file], payload)["timeSelection"],
                {"timePeriod": "l21d"},
                query_file,
            )

        self.assertIn("link", visualization_types)
        self.assertIn("line", visualization_types)
        self.assertIn("summary_table", visualization_types)

        attack_queries = {
            "apps/apm_octo_attack_timeline.json",
            "apps/apm_octo_attack_path_link.json",
            "apps/apm_octo_attack_trace_correlation.json",
            "apps/apm_octo_payment_threats.json",
            "apps/apm_octo_osquery_findings.json",
            "apps/apm_octo_compromised_vm_pivots.json",
        }
        for query_file in attack_queries:
            with (Path(QUERIES_DIR) / query_file).open() as f:
                payload = json.load(f)
            query = payload["query"]
            self.assertIn("'Attack ID'", query)
            self.assertTrue(
                any(token in query for token in (
                    "'Payment Redirect URL'",
                    "'Payment Interception'",
                    "'Compromised VM'",
                    "'OSQuery Finding'",
                    "'Attack Stage'",
                )),
                query_file,
            )

    def test_link_tile_layout_metadata_is_well_formed(self):
        expected_tile_layout_queries = {
            "apps/apm_octo_span_link.json",
            "apps/apm_octo_attack_path_link.json",
            "apps/apm_octo_trace_investigation_tiles.json",
            "apps/apm_trace_correlation_link.json",
            "hunting/bluelight_attack_path_link.json",
            "hunting/c2_communication_topology.json",
            "hunting/flf_port_knocking_sequence.json",
            "hunting/melts_attack_path_link.json",
            "hunting/web_to_cloud_attack_path_link.json",
        }
        tiled_queries = set()

        for config in DASHBOARDS.values():
            for widget in config["widgets"]:
                query_file = widget["query_file"]
                query_path = Path(QUERIES_DIR) / query_file
                with query_path.open() as f:
                    payload = json.load(f)

                dashboard_meta = payload.get("dashboard", {})
                options = dashboard_meta.get("visualizationOptions", {})
                tile_layout_xml = options.get("tileLayoutXml")
                if not tile_layout_xml:
                    continue

                tiled_queries.add(query_file)
                self.assertEqual(dashboard_meta.get("visualizationType"), "link", query_file)
                self.assertIn("Tiles", options.get("dashboardOptions", []), query_file)
                self.assertIn("Main Table", options.get("dashboardOptions", []), query_file)

                root = ET.fromstring(tile_layout_xml)
                self.assertEqual(root.tag, "summary", query_file)
                tile_fields = {
                    tile.attrib["field"]
                    for tile in root.iter("tile")
                    if tile.attrib.get("field")
                }
                self.assertGreater(len(tile_fields), 0, query_file)
                for field in tile_fields:
                    self.assertIn(f" as {field}", payload["query"], query_file)

        self.assertTrue(expected_tile_layout_queries.issubset(tiled_queries))

    def test_link_commands_stay_within_oci_field_limit(self):
        """OCI Log Analytics link commands used by dashboards support up to four fields."""
        for config in DASHBOARDS.values():
            for widget in config["widgets"]:
                query_file = widget["query_file"]
                with (Path(QUERIES_DIR) / query_file).open() as f:
                    payload = json.load(f)

                for command in payload["query"].split("|"):
                    command = command.strip()
                    if not command.lower().startswith("link "):
                        continue
                    link_fields = re.findall(r"'([^']+)'", command)
                    self.assertLessEqual(
                        len(link_fields),
                        4,
                        f"{query_file} link command exceeds OCI Log Analytics four-field LINK limit",
                    )

    def test_freelabfriday_dashboard_carries_source_references(self):
        dashboard = DASHBOARDS["SOC: FreeLabFriday Threat Hunting Dashboard"]
        expected_query_files = {
            "hunting/flf_dns_c2_pattern_analysis.json",
            "hunting/flf_bits_exfiltration.json",
            "hunting/flf_cloud_service_exfiltration.json",
            "hunting/flf_domain_fronting_cdn_c2.json",
            "hunting/flf_vsagent_http_beaconing.json",
            "hunting/flf_credential_stuffing_pattern.json",
            "hunting/flf_new_user_persistence.json",
            "hunting/flf_port_knocking_sequence.json",
        }
        actual_query_files = {widget["query_file"] for widget in dashboard["widgets"]}

        self.assertEqual(expected_query_files, actual_query_files)
        self.assertIn("FreeLabFriday", dashboard["description"])

        visualization_types = {}
        for query_file in expected_query_files:
            query_path = Path(QUERIES_DIR) / query_file
            with query_path.open() as f:
                payload = json.load(f)

            references = payload.get("references", [])
            visualization_types[query_file] = payload.get("dashboard", {}).get("visualizationType")

            self.assertTrue(references, query_file)
            self.assertTrue(payload.get("dashboard", {}).get("ask_ai_prompts"), query_file)
            for reference in references:
                self.assertTrue(
                    reference.get("url", "").startswith(
                        "https://github.com/blackhillsinfosec/FreeLabFriday_Labs"
                    ),
                    query_file,
                )

        self.assertEqual(visualization_types["hunting/flf_vsagent_http_beaconing.json"], "line")
        self.assertEqual(visualization_types["hunting/flf_port_knocking_sequence.json"], "link")
        self.assertIn("summary_table", set(visualization_types.values()))

    def test_2025_2026_dashboard_covers_modern_attack_drilldowns(self):
        dashboard = DASHBOARDS["SOC: 2025-2026 Threat Hunting Dashboard"]
        expected_query_files = {
            "hunting/melts_attack_signal_overview.json",
            "hunting/melts_attack_timeline.json",
            "hunting/melts_attack_path_link.json",
            "hunting/clickfix_clipboard_powershell_execution.json",
            "hunting/clickfix_lolbin_payload_execution.json",
            "hunting/crashfix_python_rat_activity.json",
            "hunting/sharepoint_toolshell_exploitation.json",
            "hunting/sharepoint_toolshell_webshell_post_exploit.json",
            "hunting/rmm_post_compromise_activity.json",
            "hunting/cloud_identity_aitm_token_abuse.json",
            "hunting/exfiltration_after_initial_access_2025_2026.json",
            "hunting/compromised_machines_and_data_2025_2026.json",
        }
        actual_query_files = {widget["query_file"] for widget in dashboard["widgets"]}

        self.assertEqual(expected_query_files, actual_query_files)
        self.assertLessEqual(len(dashboard["widgets"]), 30)
        self.assertIn("MELTS", dashboard["description"])

        advanced_types = set()
        source_backed_queries = set()
        for query_file in expected_query_files:
            query_path = Path(QUERIES_DIR) / query_file
            with query_path.open() as f:
                payload = json.load(f)

            advanced_types.add(payload.get("dashboard", {}).get("visualizationType"))
            self.assertEqual(payload.get("dashboard", {}).get("timeSelection"), {"timePeriod": "l21d"})
            self.assertTrue(payload.get("dashboard", {}).get("ask_ai_prompts"), query_file)
            if payload.get("references"):
                source_backed_queries.add(query_file)

        self.assertIn("link", advanced_types)
        self.assertIn("line", advanced_types)
        self.assertIn("summary_table", advanced_types)
        self.assertTrue(source_backed_queries)

    def test_dashboard_inventory_exports_source_references(self):
        inventory = build_dashboard_inventory(generated_at="2026-04-28T00:00:00+00:00")
        flf_dashboard = next(
            dashboard for dashboard in inventory["dashboards"]
            if dashboard["name"] == "SOC: FreeLabFriday Threat Hunting Dashboard"
        )

        for widget in flf_dashboard["widgets"]:
            references = widget.get("references", [])
            self.assertTrue(references, widget["query_file"])
            self.assertTrue(
                references[0]["url"].startswith(
                    "https://github.com/blackhillsinfosec/FreeLabFriday_Labs"
                ),
                widget["query_file"],
            )

    def test_dashboard_inventory_validates_every_query_reference(self):
        inventory = build_dashboard_inventory(generated_at="2026-04-28T00:00:00+00:00")

        errors = validate_dashboard_inventory(inventory)

        self.assertEqual(errors, [])

    def test_dashboard_inventory_rejects_generated_support_artifact_reference(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            queries_dir = Path(tmpdir)
            (queries_dir / "sentinel_synthetic_plan.json").write_text(
                json.dumps({
                    "summary": {"synthetic_ready": 1},
                    "candidates": [{"title": "support artifact"}],
                }),
                encoding="utf-8",
            )
            inventory = {
                "summary": {"total_dashboards": 1, "total_widgets": 1},
                "dashboards": [
                    {
                        "name": "Test Dashboard",
                        "widget_count": 1,
                        "widgets": [
                            {
                                "title": "Bad Widget",
                                "query_file": "sentinel_synthetic_plan.json",
                            }
                        ],
                    }
                ],
            }

            errors = validate_dashboard_inventory(inventory, queries_dir=str(queries_dir))

            self.assertTrue(
                any(
                    "sentinel_synthetic_plan.json" in error
                    and "generated support artifact" in error
                    for error in errors
                ),
                errors,
            )

    def test_dashboard_inventory_validation_catches_query_metadata_drift(self):
        inventory = build_dashboard_inventory(generated_at="2026-04-28T00:00:00+00:00")
        inventory["dashboards"][0]["widgets"][0]["query_title"] = "Wrong title"

        errors = validate_dashboard_inventory(inventory)

        self.assertTrue(any("query_title mismatch" in error for error in errors))

    def test_dashboard_inventory_validation_catches_layout_drift(self):
        inventory = build_dashboard_inventory(generated_at="2026-04-28T00:00:00+00:00")
        inventory["dashboards"][0]["widgets"][0]["layout"] = {"width": 6, "height": 5}

        errors = validate_dashboard_inventory(inventory)

        self.assertTrue(any("layout mismatch" in error for error in errors))

    def test_dashboard_inventory_validation_catches_visualization_drift(self):
        inventory = build_dashboard_inventory(generated_at="2026-04-28T00:00:00+00:00")
        inventory["dashboards"][0]["widgets"][0]["visualization_type"] = "bar"

        errors = validate_dashboard_inventory(inventory)

        self.assertTrue(any("visualization_type mismatch" in error for error in errors))

    def test_live_validation_progress_reports_status_and_redacts_sensitive_details(self):
        inventory = {
            "dashboards": [
                {
                    "widgets": [
                        {"query_file": "apps/one.json"},
                        {"query_file": "apps/two.json"},
                    ]
                }
            ]
        }
        validation_results = [
            {"query_file": "apps/one.json", "ok": True, "rows": 2, "empty": False},
            {
                "query_file": "apps/two.json",
                "ok": False,
                "rows": 0,
                "empty": False,
                "error": (
                    "opc-request-id: abc123 ocid1.tenancy.oc1..secret "
                    "203.0.113.44 profile DEFAULT namespace captenancy"
                ),
            },
        ]
        output = io.StringIO()

        with patch("deploy_dashboard.resolve_validation_namespace", return_value="redacted-namespace"), \
             patch("deploy_dashboard.get_la_client", return_value=object()), \
             patch("deploy_dashboard.load_query_info", return_value={"query": "'Log Source' = 'SOC Application Logs'"}), \
             patch("deploy_dashboard.validate_query_in_oci", side_effect=validation_results):
            with redirect_stdout(output):
                results = validate_inventory_queries_in_oci(
                    inventory,
                    progress=True,
                    progress_interval=1,
                    isolated=False,
                )

        rendered = output.getvalue()
        self.assertEqual(results, validation_results)
        self.assertIn("[001/002] apps/one.json status=passed rows=2", rendered)
        self.assertIn("[002/002] apps/two.json status=failed rows=0", rendered)
        self.assertNotIn("ocid1.", rendered)
        self.assertNotIn("abc123", rendered)
        self.assertNotIn("203.0.113.44", rendered)
        self.assertNotIn("DEFAULT", rendered)
        self.assertNotIn("captenancy", rendered)

    def test_sentinel_dashboard_loader_selects_diverse_live_passed_widgets(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            queries_dir = Path(tmpdir)
            sentinel_dir = queries_dir / "sentinel"
            sentinel_dir.mkdir(parents=True)

            def write_sentinel(filename, **overrides):
                payload = {
                    "title": filename.replace(".json", ""),
                    "query": "'Log Source' = 'SOC Windows Sysmon Logs' | stats count as Count",
                    "level": "high",
                    "source_type": "microsoft_sentinel",
                    "conversion_status": "promoted",
                    "live_validation_status": "passed",
                    "sentinel_category": "endpoint",
                    "sentinel_tables": ["DeviceProcessEvents"],
                    "mitre_attack": {"techniques": ["T1059"]},
                    "required_data_connectors": [
                        {"connector_id": "MicrosoftThreatProtection", "data_types": ["DeviceProcessEvents"]}
                    ],
                    "dashboard": {"visualizationType": "summary_table"},
                }
                payload.update(overrides)
                (sentinel_dir / filename).write_text(json.dumps(payload), encoding="utf-8")

            for index in range(4):
                write_sentinel(f"aaa_process_{index}.json")
            write_sentinel(
                "zzz_security_event.json",
                level="medium",
                sentinel_tables=["SecurityEvent"],
                mitre_attack={"techniques": ["T1078"]},
                required_data_connectors=[{"connector_id": "SecurityEvents", "data_types": ["SecurityEvent"]}],
            )
            write_sentinel(
                "zzz_network_event.json",
                level="low",
                sentinel_tables=["DeviceNetworkEvents"],
                mitre_attack={"techniques": ["T1041"]},
                required_data_connectors=[{"connector_id": "MicrosoftThreatProtection", "data_types": ["DeviceNetworkEvents"]}],
            )
            write_sentinel("not_promoted.json", conversion_status="skipped")
            write_sentinel("not_live_passed.json", live_validation_status="failed")
            write_sentinel("unsupported_pattern.json", query="'Log Source' = 'x' and Properties like '*bad*'")

            dashboards = load_sentinel_dashboard_groups(queries_dir=str(queries_dir), max_widgets=4)

            widgets = dashboards["SOC: Microsoft Sentinel Endpoint Converted Detections"]["widgets"]
            selected_files = {Path(widget["query_file"]).name for widget in widgets}
            self.assertEqual(len(widgets), 4)
            self.assertTrue({"zzz_security_event.json", "zzz_network_event.json"} & selected_files)
            self.assertFalse({"not_promoted.json", "not_live_passed.json", "unsupported_pattern.json"} & selected_files)

            selected_tables = set()
            for filename in selected_files:
                payload = json.loads((sentinel_dir / filename).read_text(encoding="utf-8"))
                selected_tables.update(payload["sentinel_tables"])
            self.assertGreaterEqual(len(selected_tables), 2)


if __name__ == "__main__":
    unittest.main()
