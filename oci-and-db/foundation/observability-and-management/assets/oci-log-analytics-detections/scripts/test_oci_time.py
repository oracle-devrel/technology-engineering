#!/usr/bin/env python3
"""Unit tests for OCI Log Analytics lookback helpers."""

import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oci_time import build_time_window, parse_lookback


class TestOciTime(unittest.TestCase):
    """Validate lookback parsing and absolute window generation."""

    def test_parse_lookback_supports_common_units(self):
        self.assertEqual(parse_lookback("15m"), timedelta(minutes=15))
        self.assertEqual(parse_lookback("2h"), timedelta(hours=2))
        self.assertEqual(parse_lookback("7d"), timedelta(days=7))
        self.assertEqual(parse_lookback("3w"), timedelta(weeks=3))

    def test_parse_lookback_rejects_invalid_values(self):
        for invalid in ("", "15", "1month", "-5m", "abc"):
            with self.assertRaises(ValueError, msg=invalid):
                parse_lookback(invalid)

    def test_build_time_window_returns_utc_datetimes(self):
        now = datetime(2026, 4, 15, 12, 0, tzinfo=timezone.utc)
        start, end = build_time_window("90m", now=now)

        self.assertEqual(end, now)
        self.assertEqual(start, now - timedelta(minutes=90))
        self.assertEqual(start.tzinfo, timezone.utc)
        self.assertEqual(end.tzinfo, timezone.utc)


if __name__ == "__main__":
    unittest.main()
