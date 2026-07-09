#!/usr/bin/env python3
"""Tests for end-to-end 14-day dashboard population orchestration."""

import os
import sys
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from populate_dashboard_data_14d import PROJECT_DIR, build_commands, run_commands


class TestPopulateDashboardData14d(unittest.TestCase):
    """Validate the orchestration for generation, ingestion, deployment, and readiness."""

    def test_build_commands_uses_14_day_defaults(self):
        commands = build_commands(
            Namespace(
                days=14,
                geo_interval=15,
                unhealthy_pct=7,
                degraded_pct=12,
                lookback="14d",
                skip_ingest=False,
                skip_deploy=False,
                skip_readiness=False,
                cleanup=True,
                validate=True,
            )
        )

        self.assertEqual(len(commands), 4)
        self.assertIn("generate_dashboard_data.py", str(commands[0][1]))
        self.assertEqual(
            commands[0][2:],
            [
                "--days",
                "14",
                "--geo-interval",
                "15",
                "--unhealthy-pct",
                "7",
                "--degraded-pct",
                "12",
                "--validate",
            ],
        )
        self.assertIn("ingest_test_data.py", str(commands[1][1]))
        self.assertEqual(commands[2][-1], "--cleanup")
        self.assertEqual(commands[3][-2:], ["--lookback", "14d"])

    def test_build_commands_can_skip_later_steps(self):
        commands = build_commands(
            Namespace(
                days=14,
                geo_interval=30,
                unhealthy_pct=5,
                degraded_pct=8,
                lookback="14d",
                skip_ingest=True,
                skip_deploy=True,
                skip_readiness=True,
                cleanup=False,
                validate=False,
            )
        )

        self.assertEqual(len(commands), 1)
        self.assertIn("generate_dashboard_data.py", str(commands[0][1]))

    @patch("populate_dashboard_data_14d.subprocess.run")
    def test_run_commands_executes_from_project_root(self, mock_run):
        commands = [
            [sys.executable, str(Path(PROJECT_DIR) / "scripts" / "generate_dashboard_data.py"), "--days", "14"],
            [sys.executable, str(Path(PROJECT_DIR) / "scripts" / "ingest_test_data.py")],
        ]

        run_commands(commands)

        self.assertEqual(mock_run.call_count, 2)
        for call in mock_run.call_args_list:
            self.assertEqual(call.kwargs["check"], True)
            self.assertEqual(Path(call.kwargs["cwd"]), Path(PROJECT_DIR))


if __name__ == "__main__":
    unittest.main()
