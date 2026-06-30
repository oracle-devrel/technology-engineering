#!/usr/bin/env python3
"""Unit tests for scripts/redaction.py.

Inputs deliberately contain sensitive-shaped tokens to prove redaction works; the
defining lines carry a ``# scanner-fixture`` marker so scan_sensitive_values.py
skips them (they are test data, not a leak). The fake namespace/request-id/OCID
values are structurally valid but never reference a real tenancy.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from redaction import redact_live_payload, redact_text


class TestRedaction(unittest.TestCase):
    ENDPOINT = "POST https://loganalytics.eu-frankfurt-1.oci.oraclecloud.com/20200601/namespaces/examplens001/search/actions/query"  # scanner-fixture
    BARE_NS = "resolved /namespaces/examplens002/ in the path"  # scanner-fixture
    OPC_DICT = "{'opc-request-id': 'ABCD1234EF567890ABCD1234EF567890/FEDC0987'}"  # scanner-fixture
    OCID = "ocid1.compartment.oc1..aaaaexamplecompartment0001"  # scanner-fixture

    def test_redacts_endpoint_url_including_namespace(self):
        out = redact_text(self.ENDPOINT)
        self.assertNotIn("examplens001", out)
        self.assertNotIn("oraclecloud.com", out)
        self.assertIn("<OCI_ENDPOINT>", out)

    def test_redacts_bare_namespace_path(self):
        out = redact_text(self.BARE_NS)
        self.assertNotIn("examplens002", out)
        self.assertIn("<LA_NAMESPACE>", out)

    def test_redacts_dict_style_opc_request_id(self):
        out = redact_text(self.OPC_DICT)
        self.assertNotIn("ABCD1234EF567890", out)
        self.assertIn("<OPC_REQUEST_ID>", out)

    def test_redacts_ocid(self):
        out = redact_text(self.OCID)
        self.assertNotIn("aaaaexamplecompartment0001", out)
        self.assertIn("<OCID>", out)

    def test_redact_live_payload_recurses_and_preserves_non_strings(self):
        payload = {"error": self.OPC_DICT, "items": [self.BARE_NS], "count": 5, "ok": False}  # scanner-fixture
        out = redact_live_payload(payload)
        flat = str(out)
        self.assertNotIn("examplens002", flat)
        self.assertNotIn("ABCD1234EF567890", flat)
        self.assertEqual(out["count"], 5)
        self.assertIs(out["ok"], False)

    def test_non_string_values_pass_through(self):
        self.assertIsNone(redact_text(None))
        self.assertEqual(redact_text(42), 42)
        self.assertEqual(redact_text(""), "")


if __name__ == "__main__":
    unittest.main()
