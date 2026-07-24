#!/usr/bin/env python3
"""Tests for dashboard dataset generation orchestration."""

import os
import sys
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_dashboard_data import PROJECT_DIR, build_commands, run_commands


class TestGenerateDashboardData(unittest.TestCase):
    """Ensure the dataset generator composes the right steps."""

    def test_build_commands_covers_security_and_multicloud_generation(self):
        commands = build_commands(
            Namespace(
                days=14,
                geo_interval=15,
                unhealthy_pct=7,
                degraded_pct=12,
                validate=True,
            )
        )

        self.assertEqual(len(commands), 3)
        self.assertIn("generate_test_logs.py", str(commands[0][-3]))
        self.assertEqual(commands[0][-2:], ["--days", "14"])
        self.assertIn("generate_geo_health_logs.py", str(commands[1][1]))
        self.assertIn("20160", commands[1])
        self.assertIn("15", commands[1])
        self.assertIn("7", commands[1])
        self.assertIn("12", commands[1])
        self.assertIn("validate_synthetic_logs.py", str(commands[2][1]))

    @patch("generate_dashboard_data.subprocess.run")
    def test_run_commands_executes_from_project_root(self, mock_run):
        commands = [
            [sys.executable, str(Path(PROJECT_DIR) / "scripts" / "generate_test_logs.py"), "--days", "14"],
            [sys.executable, str(Path(PROJECT_DIR) / "scripts" / "validate_synthetic_logs.py")],
        ]

        run_commands(commands)

        self.assertEqual(mock_run.call_count, 2)
        for call in mock_run.call_args_list:
            self.assertEqual(call.kwargs["check"], True)
            self.assertEqual(Path(call.kwargs["cwd"]), Path(PROJECT_DIR))


if __name__ == "__main__":
    unittest.main()
