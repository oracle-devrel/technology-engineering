#!/usr/bin/env python3
# Copyright (c) 2026 Oracle and/or its affiliates.
"""Render one initial editable OP04 IAM declaration from pinned OE."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from op04_contract import (
    ContractError,
    canonical_onboarding_branch,
    expected_paths,
    git_text,
    validate_project,
    validate_runtime_contract,
)


def repository(value: str) -> Path:
    path = Path(os.path.abspath(value)).resolve()
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
        base = git_text(repo, "rev-parse", f"{args.base_ref}^{{commit}}").strip()
        branch = git_text(repo, "branch", "--show-current").strip()
        if branch != canonical_onboarding_branch(identity.slug, base):
            raise ContractError(
                "Create and switch to the canonical OP04 onboarding branch "
                "from the exact origin/main base before rendering."
            )
        contract = validate_runtime_contract(
            repo,
            base,
            identity.environment,
        )
        catalog_path = repo / "config/projects.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        (iam_relative,) = expected_paths(identity.slug)
        if (repo / iam_relative).exists():
            raise ContractError("The OP04 project already exists.")
        original = catalog_path.read_bytes()
        generated_relative = (
            f"op04_manage_project/{identity.environment}/{identity.slug}/"
            "generated/iam.json"
        )
        try:
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
                raise ContractError("The pinned OE generator failed.")
            generated_path = repo / generated_relative
            if not generated_path.is_file():
                raise ContractError("The pinned OE generator did not render OP04 IAM.")
            manifest_path = repo / iam_relative
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            generated_path.replace(manifest_path)
            shutil.rmtree(generated_path.parent)
        finally:
            catalog_path.write_bytes(original)
        print(f"Rendered the initial OE OP04 IAM for {identity.slug}.")
        return 0
    except (ContractError, OSError, json.JSONDecodeError) as exc:
        print(f"render-op04: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
