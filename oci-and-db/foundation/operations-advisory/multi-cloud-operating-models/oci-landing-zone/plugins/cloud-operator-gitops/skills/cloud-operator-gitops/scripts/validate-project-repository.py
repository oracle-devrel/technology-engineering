#!/usr/bin/env python3
"""Validate one initialized project repository before GitHub writes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
from pathlib import Path

from project_repository_contract import (
    CODEOWNER_TOKENS,
    RepositoryContractError,
    git,
    load_initialization,
    render_codeowners,
    validate_no_placeholders,
    validate_origin,
)


BRANCH_RE = re.compile(
    r"^agent/project-handoff-(?:crq[0-9]{1,20}-)?"
    r"(?P<project>(?:dev|test|uat|prod)-"
    r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*)-[0-9a-f]{12}$"
)
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def bundle_sha(files: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    for path in sorted(files):
        digest.update(path.encode())
        digest.update(b"\0")
        digest.update(files[path])
        digest.update(b"\0")
    return digest.hexdigest()


def regular_file(path: Path) -> bool:
    try:
        info = path.lstat()
        return stat.S_ISREG(info.st_mode) and info.st_size <= 1_048_576
    except OSError:
        return False


def validate(
    repo: Path,
    deployment_contract: Path,
    handoff_json: Path,
    handoff_markdown: Path,
    project: str,
    base_ref: str,
    expected_base: str | None,
    expected_content: str | None,
) -> dict[str, object]:
    branch = git(repo, "branch", "--show-current").strip()
    branch_match = BRANCH_RE.fullmatch(branch)
    if branch_match is None or branch_match.group("project") != project:
        raise RepositoryContractError(
            "The project handoff branch is invalid."
        )
    base = git(repo, "rev-parse", f"{base_ref}^{{commit}}").strip()
    if SHA_RE.fullmatch(base) is None:
        raise RepositoryContractError("The base revision is invalid.")
    if git(repo, "rev-parse", "HEAD^{commit}").strip() != base:
        raise RepositoryContractError(
            "The handoff branch must start at the exact protected base."
        )
    initialization = load_initialization(
        deployment_contract,
        handoff_json,
        project,
    )
    validate_origin(repo, initialization)
    validate_no_placeholders(repo)
    expected_status = sorted(
        [
            " D .github/CODEOWNERS.template",
            "?? .github/CODEOWNERS",
            " M control-plane.json",
            f" M {initialization.handoff_path}",
        ]
    )
    status = sorted(
        git(
            repo,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ).splitlines()
    )
    if status != expected_status:
        raise RepositoryContractError(
            "Exactly the repository contract, CODEOWNERS, and selected "
            "handoff may change."
        )
    control_plane_path = repo / "control-plane.json"
    codeowners_path = repo / ".github/CODEOWNERS"
    handoff_path = repo / initialization.handoff_path
    for path in (control_plane_path, codeowners_path, handoff_path):
        if not regular_file(path):
            raise RepositoryContractError(
                f"Invalid initialized file: {path.name}."
            )
    control_plane_text = control_plane_path.read_text(encoding="utf-8")
    control_plane = json.loads(control_plane_text)
    if (
        control_plane.get("repository_layout")
        != initialization.repository_layout
        or control_plane.get("target_repository")
        != initialization.target_repository
        or control_plane.get("security_profile")
        != initialization.security_profile
        or re.search(r"__[A-Z0-9_]+__", control_plane_text)
    ):
        raise RepositoryContractError(
            "The initialized control-plane contract is invalid."
        )
    template = git(
        repo,
        "show",
        f"{base}:.github/CODEOWNERS.template",
    )
    expected_codeowners = render_codeowners(
        template,
        initialization,
    )
    actual_codeowners = codeowners_path.read_text(encoding="utf-8")
    if (
        actual_codeowners != expected_codeowners
        or any(token in actual_codeowners for token in CODEOWNER_TOKENS.values())
    ):
        raise RepositoryContractError(
            "The initialized CODEOWNERS file is invalid."
        )
    source_markdown = handoff_markdown.read_bytes()
    if handoff_path.read_bytes() != source_markdown:
        raise RepositoryContractError(
            "The repository handoff differs from the validated artifact."
        )
    files = {
        ".github/CODEOWNERS": codeowners_path.read_bytes(),
        ".github/CODEOWNERS.template": b"",
        "control-plane.json": control_plane_path.read_bytes(),
        initialization.handoff_path: handoff_path.read_bytes(),
    }
    content_hash = bundle_sha(files)
    if (expected_base is None) != (expected_content is None):
        raise RepositoryContractError(
            "Expected hashes must be provided together."
        )
    if expected_base is not None and (
        expected_base != base
        or expected_content != content_hash
        or SHA256_RE.fullmatch(expected_content or "") is None
    ):
        raise RepositoryContractError(
            "The confirmed repository preview has changed."
        )
    return {
        "ok": True,
        "stage": "project-repository",
        "operation": "initialize-and-handoff",
        "repository":
            f"{initialization.customer_org}/"
            f"{initialization.target_repository}",
        "branch": branch,
        "environment": initialization.identity.environment,
        "project": project,
        "base_sha": base,
        "paths": sorted(files),
        "content_sha256": content_hash,
        "handoff_sha256":
            hashlib.sha256(source_markdown).hexdigest(),
        "summary": {
            "repository_layout": initialization.repository_layout,
            "security_profile": initialization.security_profile,
            "handoff_path": initialization.handoff_path,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--deployment-contract", required=True)
    parser.add_argument("--handoff-json", required=True)
    parser.add_argument("--handoff-markdown", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--base-ref", default="origin/main")
    parser.add_argument("--expect-base-sha")
    parser.add_argument("--expect-content-sha256")
    args = parser.parse_args()
    try:
        result = validate(
            Path(os.path.abspath(args.repo)),
            Path(os.path.abspath(args.deployment_contract)),
            Path(os.path.abspath(args.handoff_json)),
            Path(os.path.abspath(args.handoff_markdown)),
            args.project,
            args.base_ref,
            args.expect_base_sha,
            args.expect_content_sha256,
        )
        print(json.dumps(result, separators=(",", ":")))
        return 0
    except (
        RepositoryContractError,
        OSError,
        json.JSONDecodeError,
    ) as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": {
                        "code": "INVALID_PROJECT_REPOSITORY",
                        "message": " ".join(str(exc).split())[:256],
                    },
                },
                separators=(",", ":"),
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
