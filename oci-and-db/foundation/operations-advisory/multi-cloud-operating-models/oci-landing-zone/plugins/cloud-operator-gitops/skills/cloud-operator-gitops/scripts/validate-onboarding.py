#!/usr/bin/env python3
# Copyright (c) 2026 Oracle and/or its affiliates.
"""Fail closed on one additive OP04 IAM declaration."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import stat
import subprocess
from pathlib import Path

from op04_contract import (
    ContractError,
    canonical_onboarding_branch,
    expected_paths,
    load_at,
    validate_project,
    validate_runtime_contract,
)


BRANCH_RE = re.compile(
    r"^agent/project-onboard-"
    r"(?P<project>(?:dev|test|uat|prod)-"
    r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*)-[0-9a-f]{12}$"
)
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GITHUB_ORIGIN_RE = re.compile(
    r"^(?:https://github\.com/|git@github\.com:|"
    r"ssh://git@github\.com/)"
    r"(?P<repository>[A-Za-z0-9][A-Za-z0-9_.-]*/"
    r"[A-Za-z0-9][A-Za-z0-9_.-]*)$"
)
SENSITIVE_RE = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|github_pat_|"
    r"gh[pousr]_[A-Za-z0-9_]{10,}|"
    r"(?i:password\s*[:=]|client_secret\s*[:=]|api_key\s*[:=])"
)


class ValidationError(ValueError):
    """A user-safe OP04 validation failure."""


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-c", "core.fsmonitor=false", *args],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
        timeout=15,
    )
    if result.returncode:
        raise ValidationError("Git validation failed.")
    return result.stdout


def bundle_sha(files: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    for path in sorted(files):
        digest.update(path.encode())
        digest.update(b"\0")
        digest.update(files[path])
        digest.update(b"\0")
    return digest.hexdigest()


def repository_slug(repo: Path) -> str:
    """Return the exact GitHub owner/repository represented by origin."""
    remote = git(repo, "remote", "get-url", "origin").strip()
    match = GITHUB_ORIGIN_RE.fullmatch(remote)
    if match is None:
        raise ValidationError("The foundation repository origin is invalid.")
    return match.group("repository").removesuffix(".git")


def iam_json(path: Path) -> tuple[str, object]:
    """Read one bounded, regular, non-sensitive editable IAM artifact."""
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > 1_048_576:
        raise ValidationError("The OP04 IAM artifact is invalid.")
    text = path.read_text(encoding="utf-8")
    if "__" in text or SENSITIVE_RE.search(text):
        raise ValidationError("The OP04 IAM artifact is invalid.")
    return text, json.loads(text)


def validate(
    repo: Path,
    base_ref: str,
    expected_base: str | None,
    expected_content: str | None,
) -> dict[str, object]:
    branch = git(repo, "branch", "--show-current").strip()
    match = BRANCH_RE.fullmatch(branch)
    if match is None:
        raise ValidationError("The OP04 onboarding branch is invalid.")
    project = match.group("project")
    identity = validate_project(project)
    base = git(repo, "rev-parse", f"{base_ref}^{{commit}}").strip()
    if SHA_RE.fullmatch(base) is None:
        raise ValidationError("The base revision is invalid.")
    if branch != canonical_onboarding_branch(project, base):
        raise ValidationError("The OP04 onboarding branch is invalid.")
    contract = validate_runtime_contract(repo, base, identity.environment)
    (manifest_relative,) = expected_paths(project)
    status = sorted(
        line
        for line in git(
            repo,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ).splitlines()
    )
    expected_status = [f"?? {manifest_relative}"]
    if status != expected_status:
        raise ValidationError("Exactly one new OP04 IAM file may change.")
    manifest_path = repo / manifest_relative
    manifest_text, manifest = iam_json(manifest_path)
    if (
        not isinstance(manifest, dict)
        or sorted(manifest) != [
            "compartments_configuration",
            "identity_domain_groups_configuration",
        ]
    ):
        raise ValidationError("The OP04 IAM manifest is invalid.")
    files = {manifest_relative: manifest_path.read_bytes()}
    content_hash = bundle_sha(files)
    if (expected_base is None) != (expected_content is None):
        raise ValidationError("Expected hashes must be provided together.")
    if expected_base is not None and (
        expected_base != base
        or expected_content != content_hash
        or SHA256_RE.fullmatch(expected_content or "") is None
    ):
        raise ValidationError("The confirmed preview has changed.")
    diff = "".join(
        difflib.unified_diff(
            [],
            manifest_text.splitlines(keepends=True),
            fromfile="/dev/null",
            tofile=f"b/{manifest_relative}",
        )
    )
    return {
        "ok": True,
        "stage": "op04",
        "operation": "project-onboard",
        "repository": repository_slug(repo),
        "branch": branch,
        "environment": identity.environment,
        "project": project,
        "base_sha": base,
        "paths": [manifest_relative],
        "content_sha256": content_hash,
        "summary": {
            "resource_type": "oci-project-foundation",
            "action": "create",
            "region": load_at(
                repo,
                base,
                contract["environment_blueprints"][identity.environment],
            )["region"],
            "state_key":
                f"op04_manage_project/{identity.environment}/"
                f"{project}/terraform.tfstate",
        },
        "diff": diff,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--base-ref", default="origin/main")
    parser.add_argument("--expect-base-sha")
    parser.add_argument("--expect-content-sha256")
    args = parser.parse_args()
    try:
        repo = Path(os.path.abspath(args.repo))
        result = validate(
            repo,
            args.base_ref,
            args.expect_base_sha,
            args.expect_content_sha256,
        )
        print(json.dumps(result, separators=(",", ":")))
        return 0
    except (ContractError, ValidationError, OSError, json.JSONDecodeError) as exc:
        message = " ".join(str(exc).split())[:256]
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": {
                        "code": "INVALID_OP04_CHANGE",
                        "message": message,
                    },
                },
                separators=(",", ":"),
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
