#!/usr/bin/env python3
"""Tests for sensitive value scanning and redaction."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scan_sensitive_values import scan_paths


SCRIPT = Path(__file__).resolve().parent / "scan_sensitive_values.py"


class TestSensitiveValueScanner(unittest.TestCase):
    """Validate finding coverage without scanning the repository."""

    def write_file(self, root: Path, relative: str, content: bytes | str) -> Path:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
        return path

    def finding_kinds(self, findings):
        return {finding["kind"] for finding in findings}

    def test_detects_private_key_blocks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_file(
                root,
                "private.pem",
                "-----BEGIN PRIVATE KEY-----\nabc123\n-----END PRIVATE KEY-----\n",  # scanner-fixture
            )

            findings = scan_paths([root])

        self.assertIn("private_key", self.finding_kinds(findings))
        self.assertEqual(findings[0]["line"], 1)
        self.assertIn("private.pem", findings[0]["path"])

    def test_detects_secret_assignments_and_redacts_previews(self):
        fixture_value = "super-secret-token-value"  # scanner-fixture
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_file(root, "settings.env", f"API_TOKEN={fixture_value}\n")

            findings = scan_paths([root])

        self.assertIn("secret_assignment", self.finding_kinds(findings))
        serialized = json.dumps(findings)
        self.assertNotIn(fixture_value, serialized)
        self.assertIn("<redacted:secret_assignment>", serialized)

    def test_allows_runtime_secret_variable_assignments(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_file(
                root,
                "session.ts",
                "const csrfToken = existingToken && existingToken.length >= 32 ? existingToken : randomBytes(32).toString('base64url')\n",
            )

            findings = scan_paths([root])

        self.assertEqual([], findings)

    def test_detects_request_ids_real_ocids_and_public_ips(self):
        request_id = "1F0DB7D0F32D4C48A6F77B3D55D1F982"  # scanner-fixture
        ocid = "ocid1.tenancy.oc1..aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"  # scanner-fixture
        ip = "8.8.8.8"  # scanner-fixture
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_file(
                root,
                "live.txt",
                f"opc-request-id: {request_id}\ntenancy={ocid}\nsource_ip={ip}\n",
            )

            findings = scan_paths([root])

        self.assertEqual({"opc_request_id", "ocid", "public_ip"}, self.finding_kinds(findings))
        serialized = json.dumps(findings)
        self.assertNotIn(request_id, serialized)
        self.assertNotIn(ocid, serialized)
        self.assertNotIn(ip, serialized)

    def test_detects_dict_style_live_payload_under_queries(self):
        # Regression: a generated report under queries/ carrying a single-quoted
        # OCI error dict (the live_validation_error leak shape) must be scanned, not
        # exempted as a query fixture, and the dict-style opc-request-id + namespace
        # must be flagged despite the quote before the colon and the '/' in the value.
        request_id = "A1B2C3D4E5F6A7B8A1B2C3D4E5F6A7B8/C9D0E1F2A3B4C5D6"  # scanner-fixture
        namespace = "qa9z3kdm7p2x"  # scanner-fixture
        leak = (
            "{\"live_validation_error\": \"{'opc-request-id': '%s', "
            "'request_endpoint': 'https://x.oci.oraclecloud.com/20200601/"
            "namespaces/%s/search'}\"}" % (request_id, namespace)
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_file(root, "queries/demo_conversion_report.json", leak)
            findings = scan_paths([root])

        kinds = self.finding_kinds(findings)
        self.assertIn("opc_request_id", kinds)
        self.assertIn("la_namespace", kinds)

    def test_allows_placeholders_example_ocids_and_documentation_ips(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_file(
                root,
                "safe.example",
                "\n".join(
                    [
                        "OCI_COMPARTMENT_ID=<COMPARTMENT_OCID>",
                        "OCI_PROFILE=<OCI_PROFILE>",
                        "tenant=ocid1.tenancy.oc1..example",
                        "source_ip=192.0.2.10",
                        "other_ip=198.51.100.25",
                        "third_ip=203.0.113.7",
                        "password=<PASSWORD>",
                    ]
                ),
            )

            findings = scan_paths([root])

        self.assertEqual([], findings)

    def test_allows_narrow_synthetic_fixture_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_file(
                root,
                "scripts/generate_test_logs.py",
                "\n".join(
                    [
                        "TENANT = 'ocid1.tenancy.oc1..aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'",
                        "ATTACKER_IP = '8.8.8.8'",
                        "CMD = 'cmd /c echo GM_ACTION_TOKEN=abc123456789'",  # scanner-fixture
                    ]
                ),
            )

            findings = scan_paths([root])

        self.assertEqual([], findings)

    def test_ignored_directories_and_binary_files_are_skipped(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_file(root, ".git/config", "token=super-secret-token-value\n")  # scanner-fixture
            self.write_file(root, ".sentinel/candidate.yaml", "password=super-secret-token-value\n")  # scanner-fixture
            self.write_file(root, "node_modules/package/config.js", "api_key=super-secret-token-value\n")  # scanner-fixture
            self.write_file(root, "blob.bin", b"\x00\x01token=super-secret-token-value")  # scanner-fixture

            findings = scan_paths([root])

        self.assertEqual([], findings)

    def test_json_cli_output_shape(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_file(root, "config.txt", "password=super-secret-token-value\n")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--json", str(root)],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["finding_count"], 1)
        self.assertEqual(payload["findings"][0]["kind"], "secret_assignment")
        self.assertNotIn("super-secret-token-value", result.stdout)


if __name__ == "__main__":
    unittest.main()
