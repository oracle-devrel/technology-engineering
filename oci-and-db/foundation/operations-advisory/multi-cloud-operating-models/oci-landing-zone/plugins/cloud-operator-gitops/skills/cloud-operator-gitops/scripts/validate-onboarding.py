#!/usr/bin/env python3
"""Fail closed on one additive, OE-generated OP04 change."""

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
    expected_paths,
    load_at,
    validate_project,
    validate_runtime_contract,
)


BRANCH_RE = re.compile(
    r"^agent/project-onboard-(?:crq[0-9]{1,20}-)?"
    r"(?P<project>(?:dev|test|uat|prod)-"
    r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*)-[0-9a-f]{12}$"
)
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
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
    contract = validate_runtime_contract(repo, base, identity.environment)
    catalog_relative, manifest_relative = expected_paths(project)
    status = sorted(
        line
        for line in git(
            repo,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ).splitlines()
    )
    expected_status = sorted(
        [f" M {catalog_relative}", f"?? {manifest_relative}"]
    )
    if status != expected_status:
        raise ValidationError(
            "Exactly the project catalog and one generated OP04 file may change."
        )
    base_catalog = load_at(repo, base, contract["project_catalog"])
    catalog_path = repo / catalog_relative
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    for environment in ("dev", "test", "uat", "prod"):
        before = base_catalog[environment]
        after = catalog[environment]
        if environment == identity.environment:
            if (
                set(after) - set(before) != {identity.project_name}
                or set(before) - set(after)
                or len(after) != len(set(after))
            ):
                raise ValidationError("The project catalog delta is invalid.")
        elif after != before:
            raise ValidationError("Another environment was modified.")
    manifest_path = repo / manifest_relative
    info = manifest_path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > 1_048_576:
        raise ValidationError("The generated OP04 manifest is invalid.")
    manifest_text = manifest_path.read_text(encoding="utf-8")
    manifest = json.loads(manifest_text)
    if (
        sorted(manifest) != [
            "compartments_configuration",
            "identity_domain_groups_configuration",
            "policies_configuration",
        ]
        or "__" in manifest_text
        or SENSITIVE_RE.search(manifest_text)
    ):
        raise ValidationError("The generated OP04 manifest is invalid.")
    files = {
        catalog_relative: catalog_path.read_bytes(),
        manifest_relative: manifest_path.read_bytes(),
    }
    content_hash = bundle_sha(files)
    if (expected_base is None) != (expected_content is None):
        raise ValidationError("Expected hashes must be provided together.")
    if expected_base is not None and (
        expected_base != base
        or expected_content != content_hash
        or SHA256_RE.fullmatch(expected_content or "") is None
    ):
        raise ValidationError("The confirmed preview has changed.")
    base_catalog_text = git(repo, "show", f"{base}:{catalog_relative}")
    diff = "".join(
        difflib.unified_diff(
            base_catalog_text.splitlines(keepends=True),
            catalog_path.read_text(encoding="utf-8").splitlines(keepends=True),
            fromfile=f"a/{catalog_relative}",
            tofile=f"b/{catalog_relative}",
        )
    )
    diff += "".join(
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
        "repository": "__CUSTOMER_ORG__/oci-landing-zone",
        "branch": branch,
        "environment": identity.environment,
        "project": project,
        "base_sha": base,
        "paths": sorted(files),
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
