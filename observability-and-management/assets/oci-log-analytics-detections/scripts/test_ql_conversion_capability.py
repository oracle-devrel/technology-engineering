import json
import tempfile
import unittest
from pathlib import Path

from scripts.analyze_ql_conversion_coverage import build_matrix
from scripts.ql.elastic import convert_elastic, convert_elastic_eql, convert_elastic_esql, convert_elastic_toml
from scripts.ql.ir import ConversionIR, FilterPredicate, PipelineStep, SourceDataset
from scripts.ql.logan_emit import emit_logan


class QLConversionCapabilityTests(unittest.TestCase):
    def test_shared_ir_emits_logan_query(self):
        ir = ConversionIR(
            source_language="elastic_esql",
            source_query="FROM logs-apm* | WHERE http.response.status_code >= 500",
            datasets=(SourceDataset(source_name="logs-apm*", oci_log_source="SOC Application Logs"),),
            predicates=(FilterPredicate("Response Code", "gte", 500), FilterPredicate("Service Name", "exists"),),
            pipeline=(
                PipelineStep("stats", "stats count as errors by 'Service Name'"),
                PipelineStep("sort", "sort -errors"),
                PipelineStep("head", "head 20"),
            ),
        )

        query = emit_logan(ir)

        self.assertEqual(
            query,
            "'Log Source' = 'SOC Application Logs' and 'Response Code' >= 500 and 'Service Name' is not null | stats count as errors by 'Service Name' | sort -errors | head 20",
        )

    def test_elastic_scan_is_aggregate_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rules = root / "rules" / "windows"
            rules.mkdir(parents=True)
            (rules / "example.toml").write_text(
                """
[rule]
name = "Do Not Persist This Synthetic Title"
type = "query"
language = "kuery"
query = '''event.code:1 and process.command_line:"do-not-persist-query-body"'''
""".strip()
            )

            payload = build_matrix(root)

        serialized = json.dumps(payload)
        self.assertIn('"total_files": 1', serialized)
        self.assertIn('"language": "elastic_toml"', serialized)
        self.assertNotIn("Do Not Persist This Synthetic Title", serialized)
        self.assertNotIn("do-not-persist-query-body", serialized)
        self.assertNotIn("example.toml", serialized)

    def test_elastic_kuery_grouped_wildcards_preserve_or_filter(self):
        response = convert_elastic(
            "event.code:1 AND process.name:powershell.exe AND process.command_line:(*enc* OR *EncodedCommand*)",
            "elastic_kuery",
        )

        self.assertEqual(response["support_level"], "partial")
        self.assertIn("'Event ID' = '1'", response["logan_query"])
        self.assertIn("'Process Name' = 'powershell.exe'", response["logan_query"])
        self.assertIn("'Command Line' like '*enc*' or 'Command Line' like '*EncodedCommand*'", response["logan_query"])

    def test_elastic_eql_sequence_maps_to_link_sequence(self):
        response = convert_elastic_eql(
            'sequence by host.name with maxspan=5m [process where process.name == "cmd.exe"] [process where process.name == "powershell.exe"]'
        )

        self.assertEqual(response["support_level"], "partial")
        self.assertIn("| link 'Host Name'", response["logan_query"])
        self.assertIn("| sequence 'Process Name' = 'cmd.exe', 'Process Name' = 'powershell.exe'", response["logan_query"])

    def test_elastic_esql_keep_and_count_distinct_are_modeled(self):
        response = convert_elastic_esql(
            "FROM logs-endpoint.events.network-*\n"
            "| WHERE destination.ip is not null and destination.port in (22, 3389)\n"
            "| STATS unique_hosts = count_distinct(host.name) BY destination.port\n"
            "| KEEP destination.port, unique_hosts\n"
            "| SORT unique_hosts DESC\n"
            "| LIMIT 10"
        )

        self.assertEqual(response["support_level"], "partial")
        self.assertIn("'Destination IP' is not null", response["logan_query"])
        self.assertIn("'Destination Port' in ('22', '3389')", response["logan_query"])
        self.assertIn("count_distinct('Host Name') as unique_hosts", response["logan_query"])
        self.assertIn("fields 'Destination Port', 'unique_hosts'", response["logan_query"])
        self.assertIn("head 10", response["logan_query"])

    def test_elastic_toml_threat_match_surfaces_lookup_dependency(self):
        response = convert_elastic_toml(
            "[rule]\n"
            "type = \"threat_match\"\n"
            "language = \"kuery\"\n"
            "query = '''source.ip:*'''\n"
        )

        self.assertEqual(response["support_level"], "lossy")
        self.assertIn("lookup <threat_lookup_name> 'Source IP'", response["logan_query"])
        self.assertIn("oci_lookup:<threat_lookup_name>", response["metadata"]["dependencies"])


if __name__ == "__main__":
    unittest.main()
