#!/usr/bin/env python3
"""Check that an approved ADB request is still current in the project repo."""

import json
import subprocess
import sys
from pathlib import PurePosixPath


def git(*args):
    return subprocess.run(
        ["git", "--literal-pathspecs", *args],
        check=True, capture_output=True, text=True, errors="surrogateescape",
    ).stdout


def adb_targets(content):
    try:
        manifest = json.loads(content)
    except json.JSONDecodeError:
        return set()
    if not isinstance(manifest, dict) or manifest.get("operation_type") != "adb-lifecycle":
        return set()
    targets = manifest.get("targets")
    if not isinstance(targets, list):
        return set()
    return {
        target["display_name"] for target in targets
        if isinstance(target, dict) and isinstance(target.get("display_name"), str)
    }


def is_current(operation):
    approved = git("rev-parse", "HEAD").strip()
    git("fetch", "--no-tags", "origin", "refs/heads/main")
    latest = git("rev-parse", "FETCH_HEAD").strip()
    git("merge-base", "--is-ancestor", approved, latest)
    scope = PurePosixPath(operation).parent
    targets = adb_targets(git("show", f"{approved}:{operation}"))

    # Walk changes as they landed on main, including requests later cleared
    # or restored with identical contents.
    commits = git("log", "--first-parent", "--format=%H", f"{approved}..{latest}", "--", str(scope))
    for commit in commits.splitlines():
        entries = git(
            "diff", "--no-renames", "--name-status", "-z", f"{commit}^1", commit, "--", str(scope),
        ).split("\0")
        for status, path in zip(entries[::2], entries[1::2]):
            if path == operation:
                return False
            # Project callers also accept other JSON filenames in this directory.
            candidate = PurePosixPath(path)
            if status != "D" and candidate.parent == scope and candidate.suffix == ".json":
                if targets & adb_targets(git("show", f"{commit}:{path}")):
                    return False
    return True


if __name__ == "__main__":
    operation = sys.argv[1]
    try:
        current = is_current(operation)
    except subprocess.CalledProcessError:
        sys.exit("Could not verify the approved ADB request against current project main.")
    if not current:
        sys.exit(f"ADB request is no longer current on project main: {operation}")
