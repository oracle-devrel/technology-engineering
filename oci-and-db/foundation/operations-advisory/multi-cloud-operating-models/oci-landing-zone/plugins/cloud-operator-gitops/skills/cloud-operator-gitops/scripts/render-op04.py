#!/usr/bin/env python3
"""Render one canonical OP04 project target from same-environment evidence."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from op04_contract import ContractError, derive_baseline, expected_files, git_text, validate_project


def repository(path: str) -> Path:
    absolute = Path(os.path.abspath(path))
    if not absolute.is_dir() or Path(git_text(absolute, "rev-parse", "--show-toplevel").strip()) != absolute:
        raise ContractError("The landing-zone repository is invalid.")
    return absolute


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--base-ref", default="origin/main")
    args = parser.parse_args()
    try:
        repo = repository(args.repo)
        identity = validate_project(args.project)
        root = repo / "op04_manage_project" / identity.environment / identity.slug
        if root.exists():
            raise ContractError("The OP04 project target already exists.")
        baseline = derive_baseline(repo, args.base_ref, identity.environment)
        files = expected_files(args.project, baseline)
        root.mkdir(parents=True, exist_ok=False)
        for relative_path, content in files.items():
            path = repo / relative_path
            path.write_bytes(content)
        print(f"Rendered {len(files)} canonical OP04 files for {args.project}.")
        return 0
    except (ContractError, OSError) as exc:
        print(f"render-op04: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
