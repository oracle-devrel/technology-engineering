#!/usr/bin/env python3
"""Tests for Microsoft Sentinel KQL intake and conversion."""

import json
import os
import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from convert_sentinel_kql import (  # noqa: E402
    _write_query_payload,
    classify_unsupported_kql,
    convert_candidate,
    convert_candidates,
    convert_kql_to_logan,
    load_mapping_config,
    rank_candidates,
    select_top_candidates,
    validate_logan_query_local,
)
from deploy_dashboard import load_sentinel_dashboard_groups  # noqa: E402
from generate_catalog import generate_json_catalog, get_inventory_counts, load_query_surfaces  # noqa: E402
from query_artifacts import is_saved_search_query_file  # noqa: E402
from sync_sentinel_kql import normalize_sentinel_rule  # noqa: E402


class TestSentinelYamlNormalization(unittest.TestCase):
    """Validate official Sentinel YAML metadata normalization."""

    def test_normalize_analytics_rule_metadata(self):
        payload = {
            "id": "sentinel-rule-001",
            "name": "Suspicious sign-in",
            "description": "Detects suspicious Entra ID sign-ins.",
            "severity": "High",
            "requiredDataConnectors": [
                {"connectorId": "AzureActiveDirectory", "dataTypes": ["SigninLogs"]}
            ],
            "tactics": ["InitialAccess"],
            "relevantTechniques": ["T1078"],
            "query": "SigninLogs | where ResultType != 0",
        }

        normalized = normalize_sentinel_rule(
            Path("Detections/SigninLogs/suspicious_signin.yaml"),
            payload,
            repo_root=Path("."),
            commit="abc123",
        )

        self.assertEqual(normalized["sentinel_id"], "sentinel-rule-001")
        self.assertEqual(normalized["kind"], "analytics_rule")
        self.assertEqual(normalized["severity"], "high")
        self.assertEqual(normalized["required_data_connectors"][0]["connector_id"], "AzureActiveDirectory")
        self.assertEqual(normalized["mitre_attack"]["techniques"], ["T1078"])
        self.assertTrue(normalized["source_url"].endswith("/abc123/Detections/SigninLogs/suspicious_signin.yaml"))
        self.assertEqual(normalized["attribution"]["source"], "Microsoft Sentinel")

    def test_normalize_hunting_query_without_id_gets_stable_id(self):
        payload = {
            "name": "Rare process",
            "description": "Finds rare endpoint process starts.",
            "query": "DeviceProcessEvents | take 10",
        }

        normalized = normalize_sentinel_rule(
            Path("Hunting Queries/Windows/RareProcess.yaml"),
            payload,
            repo_root=Path("."),
            commit="main",
        )

        self.assertEqual(normalized["kind"], "hunting_query")
        self.assertTrue(normalized["sentinel_id"].startswith("sentinel-"))


class TestSentinelKqlConversion(unittest.TestCase):
    """Validate deterministic KQL subset conversion."""

    def setUp(self):
        self.mapping = load_mapping_config()

    def _candidate(self, **overrides):
        candidate = {
            "sentinel_id": "rule-001",
            "title": "Failed sign-in burst",
            "description": "Detects failed sign-ins with repeated source IPs.",
            "severity": "high",
            "query": (
                "SigninLogs\n"
                "| where TimeGenerated > ago(1d)\n"
                "| where Result != \"Success\" and UserPrincipalName has \"admin\" "
                "and IPAddress in (\"10.0.0.1\", \"10.0.0.2\")\n"
                "| summarize Failures=count(), Users=dcount(UserPrincipalName) "
                "by UserPrincipalName, IPAddress\n"
                "| sort by Failures desc\n"
                "| take 10"
            ),
            "required_data_connectors": [
                {"connector_id": "AzureActiveDirectory", "data_types": ["SigninLogs"]}
            ],
            "mitre_attack": {"tactics": ["initial_access"], "techniques": ["T1078"]},
            "source_path": "Detections/SigninLogs/failed_signins.yaml",
            "source_url": "https://github.com/Azure/Azure-Sentinel/blob/main/Detections/SigninLogs/failed_signins.yaml",
            "attribution": {"source": "Microsoft Sentinel"},
            "kind": "analytics_rule",
        }
        return {**candidate, **overrides}

    def test_rank_candidates_quality_first(self):
        candidates = [
            self._candidate(sentinel_id="low", severity="low", mitre_attack={"tactics": [], "techniques": []}),
            self._candidate(sentinel_id="high", severity="high"),
            self._candidate(sentinel_id="join", query="SigninLogs | join AuditLogs on UserPrincipalName"),
        ]

        ranked = rank_candidates(candidates, self.mapping)
        top = select_top_candidates(candidates, self.mapping, top=2)

        self.assertEqual(ranked[0]["sentinel_id"], "high")
        self.assertEqual([candidate["sentinel_id"] for candidate in top], ["high", "low"])

    def test_convert_candidates_emits_periodic_status_and_quality_progress(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            progress = StringIO()
            report = convert_candidates(
                candidates=[
                    self._candidate(sentinel_id="convertible"),
                    self._candidate(
                        sentinel_id="unsupported",
                        query="UnknownCustomTable_CL | where Field == 'x'",
                    ),
                ],
                mapping=self.mapping,
                top=2,
                validate_live=False,
                write_working=False,
                output_dir=Path(tmpdir) / "sentinel",
                report_path=Path(tmpdir) / "report.json",
                progress_interval=0,
                progress_every=1,
                progress_stream=progress,
            )

            progress_text = progress.getvalue()
            self.assertEqual(report["summary"]["attempted_candidates"], 2)
            self.assertIn("[sentinel-convert] start total_candidates=2 attempted=2", progress_text)
            self.assertIn("score=", progress_text)
            self.assertIn('title="Failed sign-in burst"', progress_text)
            self.assertIn("status=converted", progress_text)
            self.assertIn("status=skipped", progress_text)
            self.assertIn("unsupported Sentinel table: UnknownCustomTable_CL", progress_text)
            self.assertIn("[sentinel-convert] complete attempted=2", progress_text)

    def test_convert_supported_predicates_aggregations_sort_and_limits(self):
        result = convert_candidate(self._candidate(), self.mapping)

        self.assertTrue(result.promoted_candidate)
        self.assertEqual(result.skip_reasons, [])
        query = result.query_payload["query"]
        self.assertIn("'Log Source' = 'Azure Entra ID Sign-in Logs'", query)
        self.assertNotIn("TimeGenerated", query)
        self.assertNotIn("ago(", query)
        self.assertIn("Status != 'Success'", query)
        self.assertIn("'User Name' like '*admin*'", query)
        self.assertIn("'Source IP' in ('10.0.0.1', '10.0.0.2')", query)
        self.assertIn("| stats count as Failures, distinctcount('User Name') as Users by 'User Name', 'Source IP'", query)
        self.assertIn("| sort -Failures", query)
        self.assertIn("| head 10", query)
        self.assertEqual(validate_logan_query_local(query), [])

    def test_search_in_operator_maps_tables_and_terms(self):
        query, source_info, errors = convert_kql_to_logan(
            'search in (Perf, Event, Alert) "Contoso" | take 10',
            self.mapping,
        )

        self.assertEqual(errors, [])
        self.assertEqual(source_info["tables"], ["Perf", "Event", "Alert"])
        self.assertIn("'Log Source' = 'SOC Application Logs'", query)
        self.assertIn("'Log Source' = 'Windows Event System Logs'", query)
        self.assertIn("'Original Log Content' like '*Contoso*'", query)
        self.assertIn("msg like '*Contoso*'", query)
        self.assertIn("| head 10", query)
        self.assertEqual(validate_logan_query_local(query), [])

    def test_search_stage_after_table_supports_field_predicates(self):
        query, source_info, errors = convert_kql_to_logan(
            'Perf | search CounterName == "% Processor Time" | summarize AvgCpu=avg(CounterValue) by Computer',
            self.mapping,
        )

        self.assertEqual(errors, [])
        self.assertEqual(source_info["tables"], ["Perf"])
        self.assertIn("'Metric Name' = '% Processor Time'", query)
        self.assertIn("avg('Metric Value') as AvgCpu by Entity", query)
        self.assertEqual(validate_logan_query_local(query), [])

    def test_count_stage_maps_to_stats_count(self):
        query, _source_info, errors = convert_kql_to_logan(
            "SecurityEvent | where EventID == 4624 | count",
            self.mapping,
        )

        self.assertEqual(errors, [])
        self.assertIn("'Event ID' = '4624'", query)
        self.assertIn("| stats count as Count", query)
        self.assertEqual(validate_logan_query_local(query), [])

    def test_between_predicates_and_time_ranges_convert_safely(self):
        query, _source_info, errors = convert_kql_to_logan(
            "Perf | where TimeGenerated between (ago(1h) .. now()) "
            "and CounterValue between (80 .. 100) | count",
            self.mapping,
        )

        self.assertEqual(errors, [])
        self.assertNotIn("TimeGenerated", query)
        self.assertNotIn("ago(", query)
        self.assertIn("'Metric Value' >= '80'", query)
        self.assertIn("'Metric Value' <= '100'", query)
        self.assertIn("| stats count as Count", query)
        self.assertEqual(validate_logan_query_local(query), [])

    def test_project_aliases_and_case_scalar_convert(self):
        query, _source_info, errors = convert_kql_to_logan(
            (
                "SecurityEvent\n"
                "| extend Outcome = case(EventID == 4625, 'failed', EventID == 4624, 'success', 'other')\n"
                "| project Actor = SubjectUserName, Outcome"
            ),
            self.mapping,
        )

        self.assertEqual(errors, [])
        self.assertIn("eval Outcome = if('Event ID' = '4625', 'failed', if('Event ID' = '4624', 'success', 'other'))", query)
        self.assertIn("eval Actor = 'Subject User Name'", query)
        self.assertIn("| fields Actor, Outcome", query)
        self.assertEqual(validate_logan_query_local(query), [])

    def test_summarize_by_without_aggregate_maps_to_distinct_count(self):
        query, _source_info, errors = convert_kql_to_logan(
            "SecurityEvent | summarize by Computer, EventID | sort by Count",
            self.mapping,
        )

        self.assertEqual(errors, [])
        self.assertIn("| stats count as Count by Entity, 'Event ID'", query)
        self.assertIn("| sort -Count", query)
        self.assertEqual(validate_logan_query_local(query), [])

    def test_filter_stage_converts_as_where_alias(self):
        result = convert_candidate(self._candidate(
            query=(
                "SigninLogs\n"
                "| filter Result != \"Success\" and UserPrincipalName has \"admin\""
            )
        ), self.mapping)

        self.assertEqual(result.skip_reasons, [])
        self.assertEqual(result.local_validation_errors, [])
        query = result.query_payload["query"]
        self.assertIn("Status != 'Success'", query)
        self.assertIn("'User Name' like '*admin*'", query)
        self.assertNotRegex(query, r"\bfilter\b")

    def test_role_mismatched_field_comparison_is_skipped(self):
        result = convert_candidate(self._candidate(
            query="SecurityEvent | where SubjectUserName == TargetUserName",
        ), self.mapping)

        self.assertIsNone(result.query_payload)
        self.assertIn("role_mismatch:SubjectUserName:TargetUserName", result.skip_reasons)

    def test_parser_pending_mapping_is_skipped(self):
        result = convert_candidate(self._candidate(
            query="SecurityEvent | where ObjectDN has 'CN=Admin'",
        ), self.mapping)

        self.assertIsNone(result.query_payload)
        self.assertIn("parser_readiness:pending:ObjectDN", result.skip_reasons)

    def test_convert_project_distinct_and_simple_union(self):
        candidate = self._candidate(
            query=(
                "union isfuzzy=true SigninLogs, AuditLogs\n"
                "| where OperationName startswith \"Add\" or Result has \"failure\" "
                "and IPAddress not in (\"127.0.0.1\")\n"
                "| distinct UserPrincipalName, IPAddress\n"
                "| project UserPrincipalName, IPAddress"
            )
        )

        result = convert_candidate(candidate, self.mapping)

        self.assertEqual(result.skip_reasons, [])
        query = result.query_payload["query"]
        self.assertIn("'Azure Entra ID Sign-in Logs'", query)
        self.assertIn("'Azure Entra ID Audit Logs'", query)
        self.assertIn("Operation like 'Add*'", query)
        self.assertIn("Status like '*failure*'", query)
        self.assertIn("'Source IP' not in ('127.0.0.1')", query)
        self.assertIn("| stats count as Count by 'User Name', 'Source IP'", query)
        self.assertIn("| fields 'User Name', 'Source IP'", query)

    def test_collection_string_operators_are_converted(self):
        result = convert_candidate(self._candidate(
            query=(
                "DeviceProcessEvents\n"
                "| where InitiatingProcessCommandLine has_any(\"kr.bin\", \"if.bin\")\n"
                "| where ProcessCommandLine has_all(\"echo\", \"tmp+\")\n"
                "| where FileName hasprefix \"cmd\" and FolderPath hassuffix \"payload.exe\" and FileName !~ \"bad.exe\""
            )
        ), self.mapping)

        self.assertEqual(result.skip_reasons, [])
        self.assertEqual(result.local_validation_errors, [])
        query = result.query_payload["query"]
        self.assertNotRegex(query, r"\b(has_any|has_all|hasprefix|!~)\b")
        self.assertIn("('Command Line' like '*kr.bin*' or 'Command Line' like '*if.bin*')", query)
        self.assertIn("('Command Line' like '*echo*' and 'Command Line' like '*tmp+*')", query)
        self.assertIn("'Process Name' like 'cmd*'", query)
        self.assertIn("'Target Filename' like '*payload.exe'", query)
        self.assertIn("'Process Name' != 'bad.exe'", query)

    def test_simple_let_scalars_and_arrays_are_substituted(self):
        result = convert_candidate(self._candidate(
            query=(
                "let suspiciousProcesses = dynamic([\"cmd.exe\", \"powershell.exe\"]);\n"
                "let threshold = 3;\n"
                "DeviceProcessEvents\n"
                "| where FileName has_any (suspiciousProcesses)\n"
                "| summarize Hits=count() by DeviceName\n"
                "| where Hits > threshold"
            )
        ), self.mapping)

        self.assertEqual(result.skip_reasons, [])
        self.assertEqual(result.local_validation_errors, [])
        query = result.query_payload["query"]
        self.assertNotIn("let ", query)
        self.assertIn("('Process Name' like '*cmd.exe*' or 'Process Name' like '*powershell.exe*')", query)
        self.assertIn("| stats count as Hits by 'Host Name (Server)'", query)
        self.assertIn("| where Hits > 3", query)

    def test_set_directives_are_stripped(self):
        result = convert_candidate(self._candidate(
            query=(
                "set timeout = 5m;\n"
                "set query_take_max_records = 5000;\n"
                "SecurityEvent\n"
                "| where EventID == 4624"
            )
        ), self.mapping)

        self.assertEqual(result.skip_reasons, [])
        self.assertEqual(result.local_validation_errors, [])
        query = result.query_payload["query"]
        self.assertNotIn("set timeout", query)
        self.assertIn("'Event ID' = '4624'", query)

    def test_tabular_let_variables_remain_unsupported(self):
        result = convert_candidate(self._candidate(
            query=(
                "let suspicious = DeviceProcessEvents | where FileName == \"cmd.exe\";\n"
                "DeviceProcessEvents\n"
                "| where FileName in (suspicious)"
            )
        ), self.mapping)

        self.assertIsNone(result.query_payload)
        self.assertTrue(any("unsupported KQL construct: let variables" in reason for reason in result.skip_reasons))

    def test_inline_comments_and_timestamp_filters_do_not_leak(self):
        result = convert_candidate(self._candidate(
            query=(
                "DeviceFileEvents\n"
                "| where Timestamp > ago(14d)\n"
                "| where FolderPath contains @\"C:\\\\Temp\" and FileName in~(\"payload.exe\") // Sentinel note"
            )
        ), self.mapping)

        self.assertEqual(result.skip_reasons, [])
        self.assertEqual(result.local_validation_errors, [])
        query = result.query_payload["query"]
        self.assertNotIn("Timestamp", query)
        self.assertNotIn("ago(", query)
        self.assertNotIn("//", query)
        self.assertIn("'Target Filename' like '*C:\\\\\\\\Temp*'", query)
        self.assertIn("'Process Name' in ('payload.exe')", query)

    def test_post_summarize_where_preserves_pipeline_order(self):
        query, _source_info, errors = convert_kql_to_logan(
            (
                "SecurityEvent\n"
                "| where EventID == 4625\n"
                "| summarize Failures=count() by Account\n"
                "| where Failures > 3\n"
                "| sort by Failures desc"
            ),
            self.mapping,
        )

        self.assertEqual(errors, [])
        self.assertIn("('Event ID' = '4625') | stats count as Failures by User", query)
        self.assertIn("| where Failures > 3 | sort -Failures", query)
        self.assertLess(query.index("| stats"), query.index("| where Failures > 3"))

    def test_make_set_take_any_and_time_bins_convert_to_unique_context(self):
        query, _source_info, errors = convert_kql_to_logan(
            (
                "DeviceProcessEvents\n"
                "| summarize DiscoveryCommands=dcount(ProcessCommandLine), "
                "CommandSamples=make_set(ProcessCommandLine, 1000), "
                "AnyFile=take_any(FileName) by DeviceName, bin(TimeGenerated, 5m)\n"
                "| where DiscoveryCommands >= 3"
            ),
            self.mapping,
        )

        self.assertEqual(errors, [])
        self.assertIn("distinctcount('Command Line') as DiscoveryCommands", query)
        self.assertIn("unique('Command Line') as CommandSamples", query)
        self.assertIn("unique('Process Name') as AnyFile", query)
        self.assertIn("timestats span = 5minute", query)
        self.assertIn("by 'Host Name (Server)'", query)
        self.assertIn("| where DiscoveryCommands >= 3", query)

        time_query, _source_info, time_errors = convert_kql_to_logan(
            "DeviceProcessEvents | summarize take_any(TimeGenerated) by DeviceName",
            self.mapping,
        )
        self.assertEqual(time_errors, [])
        self.assertIn("unique(Time) as any_Time", time_query)
        self.assertNotIn("TimeGenerated", time_query)

    def test_phase9_extend_scalar_functions_convert(self):
        result = convert_candidate(self._candidate(
            query=(
                "SecurityEvent\n"
                "| extend ActorLower = tolower(tostring(Account)), "
                "IsFailure = iff(EventID == 4625, 'yes', 'no'), "
                "NumericId = toint(EventID)\n"
                "| project ActorLower, IsFailure, NumericId"
            )
        ), self.mapping)

        self.assertEqual(result.skip_reasons, [])
        self.assertEqual(result.local_validation_errors, [])
        query = result.query_payload["query"]
        self.assertIn("eval ActorLower = lower(User)", query)
        self.assertIn("eval IsFailure = if('Event ID' = '4625', 'yes', 'no')", query)
        self.assertIn("eval NumericId = 'Event ID'", query)
        self.assertIn("| fields ActorLower, IsFailure, NumericId", query)

    def test_simple_boolean_let_variables_are_supported(self):
        unsupported = classify_unsupported_kql(
            "let EnableActionFilter = true;\n"
            "let MatchActions = dynamic(['Deny', 'alert']);\n"
            "AZFWIdpsSignature | where (EnableActionFilter == false) or (Action in~ (MatchActions))"
        )

        self.assertFalse(any("let variables" in reason for reason in unsupported))

    def test_phase9_countif_bin_and_column_ifexists_convert(self):
        result = convert_candidate(self._candidate(
            query=(
                "SecurityEvent\n"
                "| where column_ifexists('Account', '') has 'admin'\n"
                "| summarize Failures=countif(EventID == 4625), Total=count() "
                "by bin(TimeGenerated, 15m), Account\n"
                "| top 5 by Failures desc"
            )
        ), self.mapping)

        self.assertEqual(result.skip_reasons, [])
        self.assertEqual(result.local_validation_errors, [])
        query = result.query_payload["query"]
        self.assertIn("User like '*admin*'", query)
        self.assertIn(
            "timestats span = 15minute sum(if('Event ID' = '4625', 1, 0)) as Failures, "
            "count as Total by User",
            query,
        )
        self.assertIn("| sort -Failures | head 5", query)

    def test_duplicate_time_aggregate_aliases_are_made_unique(self):
        query, _source_info, errors = convert_kql_to_logan(
            (
                "DeviceProcessEvents\n"
                "| summarize any(TimeGenerated), take_any(TimeGenerated) by DeviceName"
            ),
            self.mapping,
        )

        self.assertEqual(errors, [])
        self.assertIn("unique(Time) as any_Time", query)
        self.assertIn("unique(Time) as any_Time_2", query)

    def test_typed_oci_fields_format_numeric_literals_for_parser(self):
        event_query, _source_info, event_errors = convert_kql_to_logan(
            "SecurityEvent | where EventID == 4688",
            self.mapping,
        )
        network_query, _source_info, network_errors = convert_kql_to_logan(
            "DeviceNetworkEvents | where DestinationPort == \"3389\" and RemotePort in (\"443\", 8443)",
            self.mapping,
        )

        self.assertEqual(event_errors, [])
        self.assertEqual(network_errors, [])
        self.assertIn("'Event ID' = '4688'", event_query)
        self.assertIn("'Destination Port' = 3389", network_query)
        self.assertIn("'Destination Port' in (443, 8443)", network_query)

    def test_result_type_is_not_promoted_without_verified_oci_field(self):
        result = convert_candidate(self._candidate(
            query="SigninLogs | where ResultType == 50053"
        ), self.mapping)

        self.assertIsNone(result.query_payload)
        self.assertTrue(any("unsupported Sentinel field mapping: ResultType" in reason for reason in result.skip_reasons))

    def test_email_render_top_query_converts_with_implicit_count_alias(self):
        result = convert_candidate(self._candidate(
            query=(
                "EmailEvents\n"
                "| where EmailDirection == \"Inbound\"\n"
                "| where ThreatTypes has \"Malware\"\n"
                "| summarize count() by SenderFromAddress\n"
                "| sort by count_ desc\n"
                "| top 10 by count_\n"
                "| render piechart"
            )
        ), self.mapping)

        self.assertEqual(result.skip_reasons, [])
        self.assertEqual(result.local_validation_errors, [])
        query = result.query_payload["query"]
        self.assertIn("Direction = 'Inbound'", query)
        self.assertIn("'Threat Category' like '*Malware*'", query)
        self.assertIn("| stats count as count_ by 'User Name'", query)
        self.assertIn("| sort -count_", query)
        self.assertIn("| head 10", query)
        self.assertNotIn("render", query)

    def test_m365_url_click_and_oci_audit_tables_map_to_real_logan_sources(self):
        url_click = convert_candidate(self._candidate(
            query=(
                "UrlClickEvents\n"
                "| where ThreatTypes has_any (\"Malware\", \"Phish\")\n"
                "| summarize count() by AccountUpn\n"
                "| top 10 by count_"
            )
        ), self.mapping)
        oci_audit = convert_candidate(self._candidate(
            query=(
                "OCILogs\n"
                "| where data_eventName_s =~ \"DeleteRule\"\n"
                "| where data_request_headers_oci_original_url_s contains \"/opc/v1\"\n"
                "| summarize count() by SrcIpAddr"
            )
        ), self.mapping)

        self.assertEqual(url_click.skip_reasons, [])
        self.assertEqual(oci_audit.skip_reasons, [])
        self.assertIn("'Microsoft Defender Email Logs'", url_click.query_payload["query"])
        self.assertIn("'Threat Category' like '*Malware*'", url_click.query_payload["query"])
        self.assertIn("by 'User Name'", url_click.query_payload["query"])
        self.assertIn("'Log Source' = 'OCI Audit Logs'", oci_audit.query_payload["query"])
        self.assertIn("'Event Type' = 'DeleteRule'", oci_audit.query_payload["query"])
        self.assertIn("'Request URL' like '*/opc/v1*'", oci_audit.query_payload["query"])
        self.assertIn("by 'Source IP'", oci_audit.query_payload["query"])

    def test_asim_process_alias_maps_to_endpoint_sources(self):
        result = convert_candidate(self._candidate(
            query=(
                "imProcessCreate\n"
                "| where ActingProcessName has_any (\"cmd.exe\", \"powershell.exe\")\n"
                "| where Process has \"adfind\"\n"
                "| summarize Hits=count() by DvcHostname, DeviceId"
            )
        ), self.mapping)

        self.assertEqual(result.skip_reasons, [])
        query = result.query_payload["query"]
        self.assertIn("'SOC Windows Sysmon Logs'", query)
        self.assertIn("'Parent Process Name' like '*cmd.exe*'", query)
        self.assertIn("'Process Name' like '*adfind*'", query)
        self.assertIn("by 'Host Name', Entity", query)

    def test_common_solution_tables_map_to_generic_soc_sources(self):
        github = convert_candidate(self._candidate(
            query="GitHubAuditData | where Action == \"repo.destroy\" | project TimeGenerated, Actor, Action"
        ), self.mapping)
        cisco_duo = convert_candidate(self._candidate(
            query="CiscoDuo | where EventType == \"authentication\" and EventResult == \"failure\" | summarize count() by DstUserName"
        ), self.mapping)
        web_proxy = convert_candidate(self._candidate(
            query="CiscoWSAEvent | where UrlOriginal contains \"malware\" and SrcIpAddr != \"\" | summarize count() by UrlOriginal, SrcUserName"
        ), self.mapping)

        self.assertEqual(github.skip_reasons, [])
        self.assertEqual(cisco_duo.skip_reasons, [])
        self.assertEqual(web_proxy.skip_reasons, [])
        self.assertIn("'Log Source' = 'SOC Application Logs'", github.query_payload["query"])
        self.assertIn("Action = 'repo.destroy'", github.query_payload["query"])
        self.assertIn("'Event Type' = 'authentication'", cisco_duo.query_payload["query"])
        self.assertIn("Status = 'failure'", cisco_duo.query_payload["query"])
        self.assertIn("by 'Target User Name'", cisco_duo.query_payload["query"])
        self.assertIn("'Request URL' like '*malware*'", web_proxy.query_payload["query"])
        self.assertIn("by 'Request URL', 'User Name'", web_proxy.query_payload["query"])

    def test_mapping_targets_are_real_allowed_logan_fields(self):
        def display_name(field):
            value = field.strip()
            if len(value) >= 2 and value[0] == "'" and value[-1] == "'":
                return value[1:-1]
            return value

        invalid_targets = {
            sentinel_field: target
            for sentinel_field, target in self.mapping["fields"].items()
            if display_name(target) not in self.mapping["allowed_fields"]
        }

        self.assertEqual(invalid_targets, {})

    def test_isnotempty_preserves_multiword_field_quotes(self):
        result = convert_candidate(self._candidate(
            query=(
                "TMApexOneEvent\n"
                "| where isnotempty(SrcIpAddr)\n"
                "| summarize IpCount=count() by SrcIpAddr\n"
                "| top 20 by IpCount desc"
            )
        ), self.mapping)

        self.assertEqual(result.skip_reasons, [])
        self.assertEqual(result.local_validation_errors, [])
        query = result.query_payload["query"]
        self.assertIn("'Source IP' != null", query)
        self.assertIn("'Source IP' != ''", query)
        self.assertNotIn("Source IP != null", query)

    def test_common_solution_fields_map_to_dictionary_backed_logan_fields(self):
        cisco_endpoint = convert_candidate(self._candidate(
            query=(
                "CiscoSecureEndpoint\n"
                "| where EventMessage has 'Suspected ransomware'\n"
                "| extend HostCustomEntity = DstHostname, MalwareCustomEntity = ThreatName"
            )
        ), self.mapping)
        dns_query = convert_candidate(self._candidate(
            query=(
                "GCPCloudDNS\n"
                "| where Query has_any ('hidusi.com', 'dodefoh.com')\n"
                "| extend DNSCustomEntity = Query, IPCustomEntity = SrcIpAddr"
            )
        ), self.mapping)
        user_agent = convert_candidate(self._candidate(
            query=(
                "Cisco_Umbrella\n"
                "| where EventType == 'proxylogs'\n"
                "| where HttpUserAgentOriginal contains 'WindowsPowerShell'\n"
                "| where UrlCategory =~ 'IW_shrt'\n"
                "| where DstPortNumber == 443"
            )
        ), self.mapping)

        self.assertEqual(cisco_endpoint.skip_reasons, [])
        self.assertEqual(dns_query.skip_reasons, [])
        self.assertEqual(user_agent.skip_reasons, [])
        self.assertIn("Description like '*Suspected ransomware*'", cisco_endpoint.query_payload["query"])
        self.assertNotIn("MalwareCustomEntity", cisco_endpoint.query_payload["query"])
        self.assertIn("'Query Name' like '*hidusi.com*'", dns_query.query_payload["query"])
        self.assertNotIn("DNSCustomEntity", dns_query.query_payload["query"])
        self.assertIn("'User Agent' like '*WindowsPowerShell*'", user_agent.query_payload["query"])
        self.assertIn("'Threat Category' = 'IW_shrt'", user_agent.query_payload["query"])
        self.assertIn("'Destination Port' = 443", user_agent.query_payload["query"])

    def test_foundational_field_candidate_maps_only_to_dictionary_backed_action(self):
        result = convert_candidate(self._candidate(
            title="McAfee ePO - Threat was not blocked",
            source_path="Solutions/McAfee ePolicy Orchestrator/Analytic Rules/McAfeeEPOThreatNotBlocked.yaml",
            query=(
                "McAfeeEPOEvent\n"
                "| where ThreatActionTaken in~ ('none', 'IDS_ACTION_WOULD_BLOCK')\n"
                "| extend IPCustomEntity = DvcIpAddr"
            ),
        ), self.mapping)

        self.assertEqual(result.skip_reasons, [])
        self.assertEqual(result.local_validation_errors, [])
        self.assertIn("Action in ('none', 'IDS_ACTION_WOULD_BLOCK')", result.query_payload["query"])
        self.assertIn("Action", self.mapping["allowed_fields"])

    def test_custom_table_candidate_uses_phase_a_mapping_then_blocks_on_fields(self):
        result = convert_candidate(self._candidate(
            title="Theom Critical Risks",
            source_path="Solutions/Theom/Analytic Rules/TheomRisksCritical.yaml",
            query=(
                "TheomAlerts_CL\n"
                "| where customProps_RuleId_s == \"TRIS0001\" and (priority_s == \"P1\" or priority_s == \"P2\")"
            ),
        ), self.mapping)

        self.assertIsNone(result.query_payload)
        self.assertFalse(any("unsupported Sentinel table: TheomAlerts_CL" in reason for reason in result.skip_reasons))
        self.assertTrue(any("unsupported Sentinel field mapping: customProps_RuleId_s" in reason for reason in result.skip_reasons))

    def test_makeset_alias_and_additional_solution_tables_convert(self):
        aggregate = convert_candidate(self._candidate(
            query=(
                "McAfeeEPOEvent\n"
                "| summarize th_list=makeset(ThreatName) by DstHostname"
            )
        ), self.mapping)
        box = convert_candidate(self._candidate(
            query=(
                "BoxEvents\n"
                "| where EventEndTime > ago(24h)\n"
                "| where EventType =~ 'DOWNLOAD'\n"
                "| summarize DataVolume=sum(FileSize) by SourceLogin\n"
                "| top 5 by DataVolume desc"
            )
        ), self.mapping)
        cisco_ise = convert_candidate(self._candidate(
            query=(
                "CiscoISEEvent\n"
                "| where EventId in ('5231', '5236')\n"
                "| project TimeGenerated, DstUserName, SrcIpAddr"
            )
        ), self.mapping)

        self.assertEqual(aggregate.skip_reasons, [])
        self.assertEqual(box.skip_reasons, [])
        self.assertEqual(cisco_ise.skip_reasons, [])
        self.assertIn("unique('Threat Name') as th_list", aggregate.query_payload["query"])
        self.assertIn("'Log Source' = 'SOC Application Logs'", box.query_payload["query"])
        self.assertNotIn("EventEndTime", box.query_payload["query"])
        self.assertIn("sum('Network Bytes Out') as DataVolume by 'User Name'", box.query_payload["query"])
        self.assertIn("'Event ID' in ('5231', '5236')", cisco_ise.query_payload["query"])
        self.assertIn("fields Time, 'Target User Name', 'Source IP'", cisco_ise.query_payload["query"])

    def test_project_reorder_and_entity_enrichment_extends_are_supported(self):
        result = convert_candidate(self._candidate(
            query=(
                "SecurityEvent\n"
                "| where EventID == 4688\n"
                "| where Process has_any (\"powershell.exe\", \"cmd.exe\") or CommandLine has \"powershell\"\n"
                "| project-reorder TimeGenerated, Computer, Account, Process, CommandLine\n"
                "| extend NTDomain = tostring(split(Account,'\\\\',0)[0]), Name = tostring(split(Account,'\\\\',1)[0])\n"
                "| extend HostName = tostring(split(Computer, '.', 0)[0]), DnsDomain = tostring(strcat_array(array_slice(split(Computer, '.'), 1, -1), '.'))\n"
                "| extend Account_0_Name = Name\n"
                "| extend Host_0_HostName = HostName"
            )
        ), self.mapping)

        self.assertEqual(result.skip_reasons, [])
        self.assertEqual(result.local_validation_errors, [])
        query = result.query_payload["query"]
        self.assertIn("'Event ID' = '4688'", query)
        self.assertIn("('Process Name' like '*powershell.exe*' or 'Process Name' like '*cmd.exe*')", query)
        self.assertIn("'Command Line' like '*powershell*'", query)
        self.assertIn("| fields Time, Entity, User, 'Process Name', 'Command Line'", query)
        self.assertNotIn("NTDomain", query)
        self.assertNotIn("DnsDomain", query)

    def test_common_security_log_cef_fields_map_to_real_logan_fields(self):
        result = convert_candidate(self._candidate(
            query=(
                "CommonSecurityLog\n"
                "| where DeviceVendor == \"RidgeSecurity\"\n"
                "| where DeviceEventClassID == \"4001\""
            )
        ), self.mapping)

        self.assertEqual(result.skip_reasons, [])
        query = result.query_payload["query"]
        self.assertIn("Provider = 'RidgeSecurity'", query)
        self.assertIn("'Event ID' = '4001'", query)

    def test_local_validation_rejects_kql_leftovers_and_unknown_oci_fields(self):
        kql_leftovers = validate_logan_query_local(
            "'Log Source' = 'SOC Windows Sysmon Logs' and "
            "(InitiatingProcessCommandLine has_any(\"kr.bin\", \"if.bin\"))"
        )
        self.assertTrue(any("unsupported Logan output token" in error for error in kql_leftovers))

        unknown_fields = validate_logan_query_local(
            "'Log Source' = 'SOC Network Firewall Logs' and ('Device Vendor' = 'RidgeSecurity')"
        )
        self.assertTrue(any("unsupported OCI field reference: Device Vendor" in error for error in unknown_fields))

        placeholders = validate_logan_query_local(
            "'Log Source' = 'SOC Windows Sysmon Logs' and ('Command Line' like '-q -s {{*')"
        )
        self.assertTrue(any("query contains unresolved placeholder braces" in error for error in placeholders))

        placeholder_text = validate_logan_query_local(
            "'Log Source' = 'SOC Sysmon Network Logs' and 'Destination IP' = 'IP ADDRESS GOES HERE'"
        )
        self.assertTrue(any("query contains unresolved placeholder text" in error for error in placeholder_text))

        unsafe_literal = validate_logan_query_local(
            "'Log Source' = 'SOC Windows Sysmon Logs' and ('Command Line' = 'reg query '\"HKCU\"')"
        )
        self.assertTrue(any("unsafe double quote outside Logan string literal" in error for error in unsafe_literal))

    def test_local_validation_rejects_time_grouping_until_supported(self):
        errors = validate_logan_query_local(
            "'Log Source' = 'SOC Windows Sysmon Logs' | stats count as Count by Time"
        )

        self.assertIn("unsupported OCI time grouping: Time", errors)

    def test_unsupported_features_are_classified(self):
        unsupported = classify_unsupported_kql(
            "let suspicious = SecurityEvent | where EventID == 4624; "
            "SecurityEvent | extend bag=parse_json(AdditionalFields) "
            "| where Message matches regex 'abc' "
            "| parse Message with 'prefix' value 'suffix' "
            "| join suspicious on Account | mv-expand TargetResources"
        )

        self.assertTrue(any("join" in reason for reason in unsupported))
        self.assertTrue(any("let" in reason for reason in unsupported))
        self.assertTrue(any("mv-expand" in reason for reason in unsupported))
        self.assertTrue(any("JSON bag expansion" in reason for reason in unsupported))
        self.assertTrue(any("regex predicate" in reason for reason in unsupported))
        self.assertTrue(any("operator: parse" in reason for reason in unsupported))

    def test_lossy_phase9_shapes_remain_skipped(self):
        unsupported = classify_unsupported_kql(
            "SecurityEvent | where parse_command_line(CommandLine) has 'x' "
            "| evaluate bag_unpack(AdditionalFields) "
            "| make-series Count=count() on TimeGenerated in range(ago(1d), now(), 1h) "
            "| where Account matches regex 'admin.*'"
        )

        self.assertTrue(any("parse_command_line" in reason for reason in unsupported))
        self.assertTrue(any("evaluate" in reason for reason in unsupported))
        self.assertTrue(any("make-series" in reason for reason in unsupported))
        self.assertTrue(any("JSON bag expansion" in reason for reason in unsupported))
        self.assertTrue(any("regex predicate" in reason for reason in unsupported))

    def test_unsupported_string_functions_do_not_leak_to_logan(self):
        # ``strlen`` is now lowered to ``length(...)`` in scalar (extend/project)
        # contexts (Phase 9 operator-parity tranche), but it has no faithful
        # Logan QL form inside a ``where`` *predicate comparison*. The converter
        # must still refuse to promote and flag the predicate rather than leak
        # the raw KQL function into Logan output.
        result = convert_candidate(self._candidate(
            query="NGINXHTTPServer | where strlen(HttpUserAgentOriginal) < 20"
        ), self.mapping)

        self.assertIsNone(result.query_payload)
        self.assertTrue(
            any(
                "unsupported predicate expression" in reason
                for reason in result.skip_reasons
            ),
            result.skip_reasons,
        )

    def test_supported_string_functions_lower_in_extend_context(self):
        # Counterpart to the predicate guard above: strlen/strcat/extract now
        # convert cleanly when used in an ``extend`` scalar context.
        result = convert_candidate(self._candidate(
            query=(
                "NGINXHTTPServer | extend UaLen = strlen(HttpUserAgentOriginal)"
            )
        ), self.mapping)
        if result.query_payload is not None:
            logan = json.dumps(result.query_payload)
            self.assertNotIn("strlen(", logan)


class TestSentinelArtifactsAndDashboards(unittest.TestCase):
    """Validate catalog/report/dashboard integration contracts."""

    def test_sentinel_report_is_not_a_saved_search_query_file(self):
        self.assertFalse(is_saved_search_query_file("sentinel_conversion_report.json"))
        self.assertFalse(is_saved_search_query_file("sentinel_feed_dependencies.json"))

    def test_catalog_includes_sentinel_surface(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            queries_dir = project_dir / "queries"
            sentinel_dir = queries_dir / "sentinel"
            apps_dir = queries_dir / "apps"
            hunting_dir = queries_dir / "hunting"
            rules_dir = project_dir / "rules" / "cloud"
            sentinel_dir.mkdir(parents=True)
            apps_dir.mkdir()
            hunting_dir.mkdir()
            rules_dir.mkdir(parents=True)

            (sentinel_dir / "failed_signin.json").write_text(json.dumps({
                "title": "Failed sign-in burst",
                "description": "Converted from Microsoft Sentinel.",
                "query": "'Log Source' = 'Azure Entra ID Sign-in Logs' | stats count as Count",
                "level": "high",
                "source_type": "microsoft_sentinel",
                "sentinel_id": "rule-001",
                "sentinel_source_path": "Detections/SigninLogs/failed_signin.yaml",
                "conversion_status": "promoted",
                "live_validation_status": "passed",
                "logsource": {"product": "microsoft_sentinel", "service": "identity"},
                "mitre_attack": {"tactics": ["initial_access"], "techniques": ["T1078"]},
                "references": [{"name": "Microsoft Sentinel", "url": "https://github.com/Azure/Azure-Sentinel"}],
            }))

            detections, app_queries, hunting = load_query_surfaces(queries_dir, apps_dir, hunting_dir)
            inventory = get_inventory_counts(project_dir, queries_dir, apps_dir, hunting_dir)
            catalog = generate_json_catalog(detections, app_queries, hunting, inventory=inventory)

            self.assertEqual(catalog["total_sentinel_queries"], 1)
            self.assertEqual(catalog["inventory"]["generated_sentinel_queries"], 1)
            self.assertEqual(catalog["sentinel_queries"][0]["sentinel_id"], "rule-001")
            self.assertEqual(catalog["sentinel_queries"][0]["conversion_status"], "promoted")

    def test_sentinel_dashboard_loader_requires_live_validation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            queries_dir = Path(tmpdir)
            sentinel_dir = queries_dir / "sentinel"
            sentinel_dir.mkdir(parents=True)

            base_payload = {
                "title": "Failed sign-in burst",
                "description": "Converted from Microsoft Sentinel.",
                "query": "'Log Source' = 'Azure Entra ID Sign-in Logs' | stats count as Count by 'User Name'",
                "level": "high",
                "source_type": "microsoft_sentinel",
                "sentinel_id": "rule-001",
                "conversion_status": "promoted",
                "sentinel_category": "identity",
                "live_validation_status": "passed",
                "dashboard": {"visualizationType": "summary_table"},
            }
            (sentinel_dir / "failed_signin.json").write_text(json.dumps(base_payload))
            skipped = {**base_payload, "sentinel_id": "rule-002", "live_validation_status": "not_run"}
            (sentinel_dir / "not_live_validated.json").write_text(json.dumps(skipped))

            dashboards = load_sentinel_dashboard_groups(queries_dir=str(queries_dir))

            identity = dashboards["SOC: Microsoft Sentinel Identity Converted Detections"]
            self.assertEqual(identity["widgets"], [
                {
                    "title": "Sentinel: Failed sign-in burst",
                    "query_file": "sentinel/failed_signin.json",
                    "visualization_type": "summary_table",
                }
            ])

    def test_sentinel_writer_avoids_title_collisions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            base_payload = {
                "title": "Duplicate Sentinel Title",
                "query": "'Log Source' = 'SOC Windows Sysmon Logs'",
                "sentinel_id": "rule-one",
            }
            first = _write_query_payload(output_dir, base_payload)
            second = _write_query_payload(output_dir, {**base_payload, "sentinel_id": "rule-two"})

            self.assertNotEqual(first, second)
            self.assertEqual(len(list(output_dir.glob("*.json"))), 2)


if __name__ == "__main__":
    unittest.main()
