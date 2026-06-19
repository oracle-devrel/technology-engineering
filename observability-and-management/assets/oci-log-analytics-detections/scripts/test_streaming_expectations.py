#!/usr/bin/env python3
"""Unit tests for streaming-config-derived validation expectations."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oci_config import (
    CORE_SOC_STREAMS,
    get_expected_connector_names,
    get_expected_stream_names,
)


class TestStreamingExpectations(unittest.TestCase):
    """Validate expected stream/connector derivation from streaming config."""

    def test_expected_streams_default_to_core_soc_set(self):
        self.assertEqual(get_expected_stream_names({}), CORE_SOC_STREAMS)

    def test_expected_streams_include_configured_soc_extras(self):
        config = {
            "soc-detection-oci-audit": {},
            "soc-detection-cloud-guard": {},
            "soc-detection-linux-audit": {},
            "soc-detection-windows-sysmon": {},
            "soc-detection-multicloud-health": {},
            "_metadata": {},
        }

        self.assertEqual(
            get_expected_stream_names(config),
            CORE_SOC_STREAMS + ["soc-detection-multicloud-health"],
        )

    def test_expected_streams_ignore_non_soc_entries(self):
        config = {
            "soc-detection-multicloud-health": {},
            "oci-unified-stream": {},
            "_metadata": {},
        }

        self.assertEqual(
            get_expected_stream_names(config),
            CORE_SOC_STREAMS + ["soc-detection-multicloud-health"],
        )

    def test_expected_connector_names_match_expected_streams(self):
        config = {
            "soc-detection-multicloud-health": {},
            "_metadata": {},
        }

        expected = [f"sch-{name}-to-la" for name in CORE_SOC_STREAMS + ["soc-detection-multicloud-health"]]
        self.assertEqual(get_expected_connector_names(config), expected)


if __name__ == "__main__":
    unittest.main()
