#!/usr/bin/env python3
"""Fail closed on governed OP04 project-retirement evidence."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


CRQ_RE = re.compile(r"^CRQ[0-9]{1,20}$")
PROJECT_RE = re.compile(r"^(?P<environment>dev|test|uat|prod)-[a-z][a-z0-9-]{0,29}$")


class RetirementError(ValueError):
    """A stable, user-safe retirement validation failure."""


def retirement_paths(project: str) -> tuple[str]:
    """Return the one editable OP04 IAM path a retirement may remove."""
    match = PROJECT_RE.fullmatch(project)
    if match is None:
        raise RetirementError("The retirement project is invalid.")
    root = f"op04_manage_project/{match.group('environment')}/{project}"
    return (f"{root}/iam.json",)


def validate_evidence(evidence: object) -> None:
    """Require every human and automation precondition before an OP04 removal."""
    if not isinstance(evidence, dict):
        raise RetirementError("Retirement evidence must be a JSON object.")
    required = {
        "workloads_empty",
        "lifecycle_requests_absent",
        "teardown_workflow_conclusion",
        "crq",
        "state_retention",
        "approved_by",
        "repository_action",
    }
    if set(evidence) != required:
        raise RetirementError("Retirement evidence is incomplete or contains unknown fields.")
    if evidence["workloads_empty"] is not True or evidence["lifecycle_requests_absent"] is not True:
        raise RetirementError("Workloads and lifecycle requests must be empty.")
    if evidence["teardown_workflow_conclusion"] != "success":
        raise RetirementError("Successful workload teardown evidence is required.")
    if not isinstance(evidence["crq"], str) or CRQ_RE.fullmatch(evidence["crq"]) is None:
        raise RetirementError("A valid CRQ is required.")
    if evidence["state_retention"] not in {"retain", "archive"}:
        raise RetirementError("Terraform state must be retained or archived separately.")
    if evidence["repository_action"] != "preserve":
        raise RetirementError("The project repository must be preserved.")
    if not isinstance(evidence["approved_by"], str) or not evidence["approved_by"].strip():
        raise RetirementError("A human platform approval is required.")


def _git(repository: Path, *arguments: str) -> str:
    result = subprocess.run(
        [
            "git",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.hooksPath=/dev/null",
            *arguments,
        ],
        cwd=repository,
        text=True,
        capture_output=True,
        timeout=15,
        check=False,
    )
    if result.returncode:
        raise RetirementError("The retirement Git change cannot be inspected.")
    return result.stdout


def validate_retirement_change(repository: Path, base_ref: str, project: str) -> None:
    """Require the exact deletion of one project IAM file."""
    (iam_path,) = retirement_paths(project)
    statuses = {
        tuple(line.split("\t", 1))
        for line in _git(
            repository,
            "diff",
            "--no-ext-diff",
            "--no-renames",
            "--name-status",
            base_ref,
            "--",
        ).splitlines()
        if line
    }
    expected_statuses = {("D", iam_path)}
    if statuses != expected_statuses:
        raise RetirementError("Retirement must delete exactly one project IAM file.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    try:
        evidence: Any = json.loads(Path(args.evidence).read_text(encoding="utf-8"))
        validate_evidence(evidence)
        validate_retirement_change(args.repository, args.base_ref, args.project)
        print(json.dumps({
            "ok": True,
            "operation": "project-retirement-precheck",
            "project": args.project,
            "paths": retirement_paths(args.project),
        }, separators=(",", ":")))
        return 0
    except (OSError, json.JSONDecodeError, RetirementError) as exc:
        print(json.dumps({"ok": False, "error": {"code": "INVALID_RETIREMENT", "message": " ".join(str(exc).split())[:256]}}, separators=(",", ":")))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
