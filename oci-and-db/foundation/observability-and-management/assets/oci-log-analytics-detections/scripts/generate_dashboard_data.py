#!/usr/bin/env python3
"""Generate synthetic dashboard data for a multi-day observability demo."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = PROJECT_DIR / "scripts"


def positive_int(value: str) -> int:
    """Parse a strictly positive integer argument."""
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be greater than 0")
    return parsed


def build_commands(args: argparse.Namespace) -> list[list[str]]:
    """Build the subprocess commands required to generate dashboard demo data."""
    commands = [
        [
            sys.executable,
            str(SCRIPTS_DIR / "generate_test_logs.py"),
            "--days",
            str(args.days),
        ],
        [
            sys.executable,
            str(SCRIPTS_DIR / "generate_geo_health_logs.py"),
            "--duration",
            str(args.days * 1440),
            "--interval",
            str(args.geo_interval),
            "--unhealthy-pct",
            str(args.unhealthy_pct),
            "--degraded-pct",
            str(args.degraded_pct),
        ],
    ]
    if args.validate:
        commands.append(
            [
                sys.executable,
                str(SCRIPTS_DIR / "validate_synthetic_logs.py"),
            ]
        )
    return commands


def run_commands(commands: list[list[str]]) -> None:
    """Run each orchestration step from the repository root."""
    for command in commands:
        print(f"$ {' '.join(command)}")
        subprocess.run(command, check=True, cwd=PROJECT_DIR)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate the synthetic datasets used by OCI Log Analytics dashboards."
    )
    parser.add_argument(
        "--days",
        type=positive_int,
        default=21,
        help="Number of days of dashboard data to generate (default: 21)",
    )
    parser.add_argument(
        "--geo-interval",
        type=positive_int,
        default=15,
        help="Minutes between multicloud health heartbeats (default: 15)",
    )
    parser.add_argument(
        "--unhealthy-pct",
        type=positive_int,
        default=7,
        help="Percentage of multicloud instances marked unreachable (default: 7)",
    )
    parser.add_argument(
        "--degraded-pct",
        type=positive_int,
        default=12,
        help="Percentage of multicloud instances marked degraded (default: 12)",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run synthetic dataset contract validation after generation",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point."""
    args = parse_args()
    run_commands(build_commands(args))


if __name__ == "__main__":
    main()
