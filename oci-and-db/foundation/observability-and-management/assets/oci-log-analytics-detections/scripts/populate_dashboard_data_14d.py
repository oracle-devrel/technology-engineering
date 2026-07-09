#!/usr/bin/env python3
"""Generate, ingest, deploy, and validate 14-day dashboard demo data."""

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
    """Build the full 14-day dashboard population workflow."""
    commands = [
        [
            sys.executable,
            str(SCRIPTS_DIR / "generate_dashboard_data.py"),
            "--days",
            str(args.days),
            "--geo-interval",
            str(args.geo_interval),
            "--unhealthy-pct",
            str(args.unhealthy_pct),
            "--degraded-pct",
            str(args.degraded_pct),
        ]
    ]

    if args.validate:
        commands[0].append("--validate")

    if not args.skip_ingest:
        commands.append([sys.executable, str(SCRIPTS_DIR / "ingest_test_data.py")])

    if not args.skip_deploy:
        deploy_command = [sys.executable, str(SCRIPTS_DIR / "deploy_dashboard.py")]
        if args.cleanup:
            deploy_command.append("--cleanup")
        commands.append(deploy_command)

    if not args.skip_readiness:
        commands.append(
            [
                sys.executable,
                str(SCRIPTS_DIR / "demo_readiness.py"),
                "--lookback",
                args.lookback,
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
        description="Populate OCI Log Analytics dashboard data for a 14-day observability demo."
    )
    parser.add_argument(
        "--days",
        type=positive_int,
        default=14,
        help="Number of days of demo data to generate (default: 14)",
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
        "--lookback",
        default="14d",
        help="Lookback window for live readiness validation (default: 14d)",
    )
    parser.add_argument(
        "--skip-ingest",
        action="store_true",
        help="Generate data only and skip OCI ingestion",
    )
    parser.add_argument(
        "--skip-deploy",
        action="store_true",
        help="Skip dashboard redeployment",
    )
    parser.add_argument(
        "--skip-readiness",
        action="store_true",
        help="Skip post-deploy readiness checks",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate synthetic datasets before ingesting them",
    )
    parser.add_argument(
        "--cleanup",
        dest="cleanup",
        action="store_true",
        help="Delete and redeploy older saved searches and dashboards first",
    )
    parser.add_argument(
        "--no-cleanup",
        dest="cleanup",
        action="store_false",
        help="Keep existing dashboards and only upsert matching content",
    )
    parser.set_defaults(cleanup=True)
    return parser.parse_args()


def main() -> None:
    """Entry point."""
    args = parse_args()
    run_commands(build_commands(args))


if __name__ == "__main__":
    main()
