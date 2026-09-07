#!/usr/bin/env python3
"""Fail-closed validation of a shared-nonprod-v2 project change."""
import argparse
import json
import re
from pathlib import Path

ALLOWED = {"dev", "test", "uat"}
PATH = re.compile(r"^(oci|azure|gcp)/(dev|test|uat)/([^/]+)/.+\.json$")
PLACEHOLDER = re.compile(r"__[A-Z][A-Z0-9_]{2,99}__")


def fail(message: str) -> None:
    raise SystemExit(f"shared layout validation failed: {message}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("repository", type=Path)
    parser.add_argument("--paths", nargs="+", required=True)
    args = parser.parse_args()
    repository = args.repository.resolve()
    name = repository.name
    if not re.fullmatch(r"nonprod-[a-z][a-z0-9-]*", name):
        fail("repository name must be nonprod-<project>")
    tuples = set()
    for path in args.paths:
        match = PATH.fullmatch(path)
        if not match:
            fail(f"invalid shared manifest path: {path}")
        cloud, environment, region = match.groups()
        if environment not in ALLOWED:
            fail("environment is not allowed")
        handoff = repository / "environments" / environment / "environment_information.md"
        if not handoff.is_file():
            fail("environment handoff is missing")
        document = json.loads((repository / path).read_text())
        tokens = PLACEHOLDER.findall(json.dumps(document))
        for token in tokens:
            if not token.startswith(f"__{environment.upper()}_"):
                fail("placeholder is not qualified for the selected environment")
        tuples.add((cloud, environment, region))
    if len(tuples) != 1:
        fail("a change must target exactly one cloud/environment/region tuple")


if __name__ == "__main__":
    main()
