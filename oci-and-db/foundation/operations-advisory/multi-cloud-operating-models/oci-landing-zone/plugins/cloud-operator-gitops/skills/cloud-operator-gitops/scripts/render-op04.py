#!/usr/bin/env python3
"""Add one project declaration and invoke the pinned foundation generator."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from op04_contract import (
    ContractError,
    expected_paths,
    git_text,
    validate_project,
    validate_runtime_contract,
)


def repository(value: str) -> Path:
    path = Path(os.path.abspath(value))
    if (
        not path.is_dir()
        or Path(git_text(path, "rev-parse", "--show-toplevel").strip()) != path
    ):
        raise ContractError("The landing-zone repository is invalid.")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--base-ref", default="origin/main")
    args = parser.parse_args()
    try:
        repo = repository(args.repo)
        identity = validate_project(args.project)
        contract = validate_runtime_contract(
            repo,
            args.base_ref,
            identity.environment,
        )
        catalog_path = repo / contract["project_catalog"]
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        if identity.project_name in catalog[identity.environment]:
            raise ContractError("The OP04 project already exists.")
        _, manifest_relative = expected_paths(identity.slug)
        if (repo / manifest_relative).exists():
            raise ContractError("The generated OP04 target already exists.")
        original = catalog_path.read_bytes()
        catalog[identity.environment].append(identity.project_name)
        catalog[identity.environment].sort()
        catalog_path.write_text(
            json.dumps(catalog, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                "bash",
                "scripts/generate_foundation.sh",
                f"op04:{identity.slug}",
            ],
            cwd=repo,
            check=False,
        )
        if result.returncode:
            catalog_path.write_bytes(original)
            raise ContractError("The pinned OE generator failed.")
        print(f"Rendered the canonical OP04 declaration for {identity.slug}.")
        return 0
    except (ContractError, OSError, json.JSONDecodeError) as exc:
        print(f"render-op04: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
