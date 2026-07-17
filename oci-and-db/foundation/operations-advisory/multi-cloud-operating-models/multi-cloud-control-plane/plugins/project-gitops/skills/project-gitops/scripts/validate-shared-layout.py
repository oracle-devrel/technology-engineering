#!/usr/bin/env python3
"""Fail-closed validation of a shared-nonprod-v2 project change."""
import argparse
import json
import re
from pathlib import Path

ALLOWED = {"dev", "test", "uat"}
PATH = re.compile(r"^(oci|azure|gcp)/(dev|test|uat)/([^/]+)/.+\.json$")


def fail(message: str) -> None:
    raise SystemExit(f"shared layout validation failed: {message}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("repository", type=Path)
    parser.add_argument("--paths", nargs="+", required=True)
    args = parser.parse_args()
    repository = args.repository.resolve()
    name = repository.name
    if not re.fullmatch(r"oe-nonprod-[a-z][a-z0-9-]*", name):
        fail("repository name must be oe-nonprod-<project>")
    contract = json.loads((repository / "control-plane.json").read_text())
    if contract.get("repository_layout") != "shared-nonprod-v2" or contract.get("target_repository") != name:
        fail("protected layout contract does not match repository")
    tuples = set()
    for path in args.paths:
        match = PATH.fullmatch(path)
        if not match:
            fail(f"invalid shared manifest path: {path}")
        cloud, environment, region = match.groups()
        if environment not in ALLOWED or environment not in contract.get("allowed_environments", []):
            fail("environment is not allowed")
        config = contract.get("environments", {}).get(environment, {})
        if cloud not in config.get("supported_clouds", []):
            fail("cloud is not supported for environment")
        handoff = repository / "environments" / environment / "environment_information.md"
        if not handoff.is_file():
            fail("environment handoff is missing")
        tuples.add((cloud, environment, region))
    if len(tuples) != 1:
        fail("a change must target exactly one cloud/environment/region tuple")


if __name__ == "__main__":
    main()
