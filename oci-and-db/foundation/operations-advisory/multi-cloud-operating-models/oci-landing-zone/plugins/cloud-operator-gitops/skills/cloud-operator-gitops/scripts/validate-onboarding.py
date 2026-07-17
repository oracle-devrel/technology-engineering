#!/usr/bin/env python3
"""Fail-closed validation of one additive OP04 landing-zone change."""
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
from typing import NoReturn

from op04_contract import ContractError, derive_baseline, expected_files, validate_project

MAX_FILE_BYTES = 1_048_576
MAX_DIFF_BYTES = 131_072
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
PROJECT = r"oe-(?:prod|dev)-[a-z][a-z0-9]*(?:-[a-z0-9]+)*"
BRANCH_RE = re.compile(rf"^agent/project-onboard-(?:crq[0-9]{{1,20}}-)?(?P<project>{PROJECT})-[0-9a-f]{{12}}$")
ORIGIN_PREFIXES = (
    "https://github.com/__CUSTOMER_ORG__/",
    "git@github.com:__CUSTOMER_ORG__/",
    "ssh://git@github.com/__CUSTOMER_ORG__/",
)
SENSITIVE_RE = re.compile(r"(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|github_pat_|gh[pousr]_[A-Za-z0-9_]{10,}|(?i:password\s*[:=]|client_secret\s*[:=]|api_key\s*[:=]))")


class ValidationFailure(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def fail(code: str, message: str) -> NoReturn:
    raise ValidationFailure(code, message)


def emit_error(error: ValidationFailure) -> int:
    message = " ".join(error.message.split()).encode("ascii", "replace").decode("ascii")[:256]
    print(json.dumps({"ok": False, "error": {"code": error.code, "message": message}}, separators=(",", ":")))
    return 2


def run_git(repo: Path, *args: str) -> bytes:
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_OPTIONAL_LOCKS": "0", "LC_ALL": "C"})
    try:
        result = subprocess.run(["git", "-c", "core.fsmonitor=false", "-c", f"core.hooksPath={os.devnull}", "-c", "core.pager=cat", *args], cwd=repo, env=environment, stdin=subprocess.DEVNULL, capture_output=True, timeout=15, check=False)
    except (OSError, subprocess.SubprocessError) as error:
        raise ValidationFailure("GIT_FAILED", "Git validation failed.") from error
    if result.returncode or len(result.stdout) > MAX_FILE_BYTES:
        fail("GIT_FAILED", "Git validation failed.")
    return result.stdout


def git_text(repo: Path, *args: str) -> str:
    return run_git(repo, *args).decode("utf-8", errors="strict")


def repository(value: str) -> Path:
    absolute = Path(os.path.abspath(value))
    try:
        resolved = absolute.resolve(strict=True)
    except OSError as error:
        raise ValidationFailure("INVALID_REPOSITORY", "The landing-zone worktree is invalid.") from error
    if resolved != absolute or not absolute.is_dir() or git_text(absolute, "rev-parse", "--show-toplevel").strip() != str(absolute):
        fail("INVALID_REPOSITORY", "The landing-zone worktree is invalid.")
    return absolute


def require_landing_zone_origin(repo: Path) -> None:
    origin = git_text(repo, "remote", "get-url", "origin").strip()
    for prefix in ORIGIN_PREFIXES:
        if origin in {prefix + "oci-landing-zone", prefix + "oci-landing-zone.git"}:
            return
    fail("INVALID_ORIGIN", "The landing-zone repository origin is not allowed.")


def safe_file(repo: Path, relative_path: str) -> bytes:
    path = repo / relative_path
    try:
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_FILE_BYTES:
            fail("INVALID_PATH", "An OP04 file is invalid.")
        return path.read_bytes()
    except OSError as error:
        raise ValidationFailure("INVALID_PATH", "An OP04 file is invalid.") from error


def bundle_sha(files: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    for path in sorted(files):
        digest.update(path.encode()); digest.update(b"\0"); digest.update(files[path]); digest.update(b"\0")
    return digest.hexdigest()


def validate(repo: Path, base_ref: str, expected_base: str | None, expected_content: str | None) -> dict[str, object]:
    require_landing_zone_origin(repo)
    branch = git_text(repo, "branch", "--show-current").strip()
    match = BRANCH_RE.fullmatch(branch)
    if match is None:
        fail("INVALID_BRANCH", "The OP04 onboarding branch is invalid.")
    project = match.group("project")
    identity = validate_project(project)
    base = git_text(repo, "rev-parse", f"{base_ref}^{{commit}}").strip()
    if SHA_RE.fullmatch(base) is None:
        fail("INVALID_BASE_SHA", "The base commit is invalid.")
    baseline = derive_baseline(repo, base, identity.environment)
    expected = expected_files(project, baseline)
    records = run_git(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all").split(b"\0")[:-1]
    if sorted(item.decode() for item in records) != [f"?? {path}" for path in sorted(expected)]:
        fail("INVALID_CHANGE", "Exactly the canonical additive OP04 files are allowed.")
    if git_text(repo, "ls-tree", "-r", "--name-only", base, "--", f"op04_manage_project/{identity.environment}/{project}"):
        fail("EXISTING_PROJECT", "The OP04 project already exists.")
    actual = {path: safe_file(repo, path) for path in expected}
    if actual != expected or any(SENSITIVE_RE.search(content.decode("utf-8")) for content in actual.values()):
        fail("INVALID_OP04_CHANGE", "The OP04 files do not match the canonical contract.")
    content_hash = bundle_sha(actual)
    if (expected_base is None) != (expected_content is None):
        fail("INVALID_EXPECTATION", "Expected hashes must be provided together.")
    if expected_base is not None and (expected_base != base or expected_content != content_hash or SHA256_RE.fullmatch(expected_content or "") is None):
        fail("PREVIEW_DRIFT", "The expected preview no longer matches.")
    diff = "".join("".join(difflib.unified_diff([], actual[path].decode().splitlines(keepends=True), fromfile="/dev/null", tofile=f"b/{path}")) for path in sorted(actual))
    if len(diff.encode()) > MAX_DIFF_BYTES:
        fail("DIFF_SIZE_LIMIT", "The onboarding diff exceeded its limit.")
    return {"ok": True, "stage": "op04", "operation": "project-onboard", "repository": "__CUSTOMER_ORG__/oci-landing-zone", "branch": branch, "environment": identity.environment, "project": project, "base_sha": base, "paths": sorted(actual), "content_sha256": content_hash, "summary": {"resource_type": "oci-project-foundation", "action": "create", "region": baseline.region, "state_key": f"op04_manage_project/{identity.environment}/{project}/terraform.tfstate"}, "diff": diff}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--repo", required=True)
    result.add_argument("--base-ref", default="origin/main")
    result.add_argument("--expect-base-sha")
    result.add_argument("--expect-content-sha256")
    return result


def main(argv: list[str] | None = None) -> int:
    try:
        args = parser().parse_args(argv)
        print(json.dumps(validate(repository(args.repo), args.base_ref, args.expect_base_sha, args.expect_content_sha256), separators=(",", ":")))
        return 0
    except ContractError as error:
        return emit_error(ValidationFailure("INVALID_OP04_BASELINE", str(error)))
    except ValidationFailure as error:
        return emit_error(error)
    except Exception:
        return emit_error(ValidationFailure("INTERNAL_ERROR", "Validation failed safely."))


if __name__ == "__main__":
    raise SystemExit(main())
