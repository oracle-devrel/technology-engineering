import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = PROJECT_ROOT / "queries" / "logan_ql_reference_catalog.json"
PATTERNS_PATH = PROJECT_ROOT / "queries" / "cross_ql_mapping_patterns.json"
EXAMPLES_PATH = PROJECT_ROOT / "queries" / "conversion_examples.json"
CAPABILITY_PATH = PROJECT_ROOT / "queries" / "ql_conversion_capability_matrix.json"


class LoganWorkbenchArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        missing = [path for path in (REFERENCE_PATH, PATTERNS_PATH, EXAMPLES_PATH, CAPABILITY_PATH) if not path.exists()]
        if missing:
            subprocess.run(
                [sys.executable, "scripts/generate_logan_workbench_artifacts.py"],
                cwd=PROJECT_ROOT,
                check=True,
            )
        cls.reference = json.loads(REFERENCE_PATH.read_text())
        cls.patterns = json.loads(PATTERNS_PATH.read_text())
        cls.examples = json.loads(EXAMPLES_PATH.read_text())
        cls.capabilities = json.loads(CAPABILITY_PATH.read_text())

    def test_reference_catalog_has_required_official_provenance(self):
        self.assertEqual(self.reference["schema_version"], "1.0.0")
        self.assertIn("https://docs.oracle.com/en-us/iaas/log-analytics/doc/query-search.html", self.reference["sources"])
        self.assertIn(
            "https://docs.oracle.com/en-us/iaas/log-analytics/doc/command-reference.html",
            self.reference["sources"],
        )
        by_name = {entry["name"]: entry for entry in self.reference["commands"]}
        for command in self.reference["required_commands"]:
            self.assertIn(command, by_name)
            self.assertTrue(by_name[command]["summary"])
            self.assertTrue(by_name[command]["syntax"])
            self.assertTrue(by_name[command]["source_url"].startswith("https://docs.oracle.com/"))
            self.assertIn("official_command_reference", by_name[command]["provenance"])

    def test_mapping_patterns_cover_supported_source_families(self):
        languages = {pattern["source_language"] for pattern in self.patterns["patterns"]}
        self.assertIn("splunk_spl", languages)
        self.assertIn("sentinel_kql", languages)
        self.assertIn("sigma_yaml", languages)
        self.assertIn("elastic_lucene", languages)
        self.assertIn("elastic_esql", languages)
        self.assertIn("elastic_toml", languages)
        self.assertIn("cross_ql", languages)
        self.assertTrue(any(pattern["support_level"] == "unsupported" for pattern in self.patterns["patterns"]))
        for pattern in self.patterns["patterns"]:
            self.assertTrue(pattern["logan_commands"])
            self.assertTrue(pattern["warning_behavior"])

    def test_examples_are_bounded_and_cover_languages(self):
        examples = self.examples["examples"]
        self.assertGreaterEqual(len(examples), 10)
        self.assertLessEqual(len(examples), 20)
        languages = {example["source_language"] for example in examples}
        self.assertTrue(
            {
                "sigma_yaml",
                "sentinel_kql",
                "splunk_spl",
                "elastic_lucene",
                "elastic_kuery",
                "elastic_esql",
                "elastic_toml",
                "oci_logan",
            }.issubset(languages)
        )
        self.assertTrue(any(example["support_level"] == "unsupported" for example in examples))
        pattern_ids = {pattern["id"] for pattern in self.patterns["patterns"]}
        for example in examples:
            self.assertTrue(example["source_query"])
            self.assertTrue(example["explanation"])
            self.assertTrue(set(example["pattern_ids"]).issubset(pattern_ids))

    def test_capability_matrix_excludes_third_party_rule_content(self):
        self.assertEqual(self.capabilities["schema_version"], "1.0.0")
        self.assertEqual(self.capabilities["content_policy"]["third_party_rule_content"], "excluded")
        languages = {entry["language"] for entry in self.capabilities["source_capabilities"]}
        self.assertTrue({"elastic_toml", "elastic_kuery", "elastic_esql", "osquery_sql", "yara"}.issubset(languages))
        serialized = json.dumps(self.capabilities).lower()
        for forbidden_key in ("query_bodies", "rule_names", "descriptions", "notes"):
            self.assertIn(forbidden_key, serialized)
        self.assertNotIn("query = '''", serialized)


class LoganWorkbenchConverterTests(unittest.TestCase):
    def run_converter(self, payload):
        result = subprocess.run(
            [sys.executable, "scripts/logan_workbench_convert.py"],
            cwd=PROJECT_ROOT,
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
        self.assertIn(result.returncode, {0, 2}, result.stderr)
        return json.loads(result.stdout)

    def test_sigma_conversion_uses_backend_script(self):
        payload = {
            "source_language": "sigma_yaml",
            "source_query": "\n".join(
                [
                    "title: Test Encoded PowerShell",
                    "id: test-encoded-powershell",
                    "logsource:",
                    "  product: windows",
                    "  category: process_creation",
                    "detection:",
                    "  selection:",
                    "    Image|endswith: '\\\\powershell.exe'",
                    "    CommandLine|contains: ' -enc '",
                    "  condition: selection",
                    "level: high",
                ]
            ),
        }
        response = self.run_converter(payload)
        self.assertEqual(response["support_level"], "supported")
        self.assertIn("'Log Source'", response["logan_query"])
        self.assertIn("'Command Line'", response["logan_query"])
        self.assertIn("convert_sigma.py", response["explanation"])

    def test_kql_conversion_uses_sentinel_converter(self):
        response = self.run_converter(
            {
                "source_language": "sentinel_kql",
                "source_query": "SecurityEvent\n| where EventID == 4688\n| where CommandLine has \" -enc \"",
            }
        )
        self.assertEqual(response["support_level"], "supported")
        self.assertIn("Windows Security Events", response["logan_query"])
        self.assertIn("Sentinel-to-OCI KQL conversion pipeline", response["explanation"])

    def test_kql_search_in_operator_converts_through_backend(self):
        response = self.run_converter(
            {
                "source_language": "sentinel_kql",
                "source_query": 'search in (Perf, Event, Alert) "Contoso" | take 10',
            }
        )
        self.assertEqual(response["support_level"], "supported")
        self.assertIn("SOC Application Logs", response["logan_query"])
        self.assertIn("Windows Event System Logs", response["logan_query"])
        self.assertIn("'Original Log Content' like '*Contoso*'", response["logan_query"])
        self.assertIn("msg like '*Contoso*'", response["logan_query"])
        self.assertIn("| head 10", response["logan_query"])

    def test_elastic_esql_pipeline_converts_through_backend(self):
        response = self.run_converter(
            {
                "source_language": "elastic_esql",
                "source_query": "FROM logs-apm*\n| WHERE http.response.status_code >= 500 and service.name is not null\n| STATS errors = count(*) BY service.name\n| SORT errors DESC\n| LIMIT 20",
            }
        )
        self.assertEqual(response["support_level"], "partial")
        self.assertIn("'Log Source' = 'SOC Application Logs'", response["logan_query"])
        self.assertIn("'Response Code' >= 500", response["logan_query"])
        self.assertIn("stats count as errors by 'Service Name'", response["logan_query"])
        self.assertIn("head 20", response["logan_query"])

    def test_elastic_toml_threshold_dispatches_without_persistence(self):
        response = self.run_converter(
            {
                "source_language": "elastic_toml",
                "source_query": "[rule]\ntype = \"threshold\"\nlanguage = \"kuery\"\nquery = '''event.category:authentication and event.outcome:failure'''\n\n[rule.threshold]\nfield = [\"source.ip\", \"user.name\"]\nvalue = 5",
            }
        )
        self.assertEqual(response["support_level"], "lossy")
        self.assertIn("'Log Source' = 'OCI Audit Logs'", response["logan_query"])
        self.assertIn("stats count as event_count by 'Source IP', 'User Name'", response["logan_query"])
        self.assertEqual(response["metadata"]["third_party_content_policy"], "request_only_no_persistence")

    def test_osquery_and_yara_boundaries_are_explicit(self):
        for language, source_query, code in (
            ("osquery_sql", "select * from processes where name = 'sh';", "unsupported_stateful_query"),
            ("yara", "rule TestRule { condition: true }", "unsupported_content_scan"),
        ):
            with self.subTest(language=language):
                response = self.run_converter({"source_language": language, "source_query": source_query})
                self.assertEqual(response["support_level"], "unsupported")
                self.assertEqual(response["logan_query"], "")
                self.assertEqual(response["warnings"][0]["code"], code)

    def test_unsafe_yaml_is_blocked(self):
        response = self.run_converter(
            {
                "source_language": "sigma_yaml",
                "source_query": "!!python/object/apply:os.system ['id']",
            }
        )
        self.assertEqual(response["support_level"], "unsupported")
        self.assertEqual(response["warnings"][0]["code"], "unsafe_yaml_tag")

    def test_all_published_examples_exercise_conversion_boundary(self):
        examples = json.loads(EXAMPLES_PATH.read_text())["examples"]
        self.assertGreaterEqual(len(examples), 10)
        for example in examples:
            with self.subTest(example=example["id"]):
                response = self.run_converter(
                    {
                        "source_language": example["source_language"],
                        "source_query": example["source_query"],
                    }
                )
                if example["support_level"] == "unsupported":
                    self.assertEqual(response["support_level"], "unsupported")
                    self.assertEqual(response["logan_query"], "")
                else:
                    self.assertIn(response["support_level"], {"supported", "partial", "lossy"})
                    self.assertIn("'Log Source'", response["logan_query"])


if __name__ == "__main__":
    unittest.main()
