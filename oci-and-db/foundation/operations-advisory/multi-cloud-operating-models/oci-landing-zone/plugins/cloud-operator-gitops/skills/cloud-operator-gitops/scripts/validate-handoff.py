#!/usr/bin/env python3
"""Validate environment-aware OCI project handoff artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


PROJECT_RE = re.compile(
    r"^(?P<environment>dev|test|uat|prod)-"
    r"(?P<name>[a-z][a-z0-9]*(?:-[a-z0-9]+)*)$"
)
REGION_RE = re.compile(r"^[a-z]{2}-[a-z]+-[0-9]+$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
OCID_PREFIXES = {
    "app_compartment": "ocid1.compartment.",
    "database_compartment": "ocid1.compartment.",
    "infrastructure_compartment": "ocid1.compartment.",
    "vcn": "ocid1.vcn.",
}
REQUIRED = {
    "schema_version", "cloud", "project_slug", "environment", "region",
    "app_compartment", "database_compartment", "infrastructure_compartment",
    "vcn", "subnets", "source_repository", "source_workflow", "source_run",
    "source_commit", "op02_state_key", "op04_state_key", "repository_layout",
    "target_repository", "handoff_path",
}
SENSITIVE_RE = re.compile(
    r"(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|github_pat_|gh[pousr]_[A-Za-z0-9_]{10,}|"
    r"(?i:password\s*[:=]|client_secret\s*[:=]|api_key\s*[:=]))"
)


def fail(message: str) -> None:
    raise ValueError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--handoff-json", required=True, type=Path)
    parser.add_argument("--handoff-markdown", required=True, type=Path)
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    try:
        match = PROJECT_RE.fullmatch(args.project)
        if match is None or len(match.group("name")) > 30:
            fail("invalid environment-specific foundation project")
        environment = match.group("environment")
        project_name = match.group("name")
        target = f"prod-{project_name}" if environment == "prod" else f"nonprod-{project_name}"
        layout = "production-v1" if environment == "prod" else "shared-nonprod-v2"
        handoff_path = f"environments/{environment}/environment_information.md"
        data = json.loads(args.handoff_json.read_text(encoding="utf-8"))
        markdown = args.handoff_markdown.read_text(encoding="utf-8")
        if not isinstance(data, dict) or set(data) != REQUIRED:
            fail("handoff JSON fields do not match schema version 2")
        if (
            data["schema_version"] != 2
            or data["cloud"] != "oci"
            or data["environment"] != environment
            or data["project_slug"] != target
            or data["target_repository"] != target
            or data["repository_layout"] != layout
            or data["handoff_path"] != handoff_path
            or not REGION_RE.fullmatch(str(data["region"]))
        ):
            fail("handoff routing does not match the foundation project")
        if (
            data["op02_state_key"]
            != f"op02_manage_environment/{environment}/terraform.tfstate"
            or data["op04_state_key"]
            != f"op04_manage_project/{environment}/{args.project}/terraform.tfstate"
        ):
            fail("handoff state provenance is invalid")
        if (
            not REPOSITORY_RE.fullmatch(str(data["source_repository"]))
            or not str(data["source_run"]).isdigit()
            or not COMMIT_RE.fullmatch(str(data["source_commit"]))
            or not isinstance(data["source_workflow"], str)
            or not data["source_workflow"]
        ):
            fail("handoff source provenance is invalid")
        for field, prefix in OCID_PREFIXES.items():
            if not isinstance(data[field], str) or not data[field].startswith(prefix):
                fail(f"invalid {field}")
        if not isinstance(data["subnets"], dict) or not data["subnets"]:
            fail("handoff subnets are invalid")
        for value in data["subnets"].values():
            if not isinstance(value, str) or not value.startswith("ocid1.subnet."):
                fail("handoff subnet OCID is invalid")
        expected_markdown_values = [args.project, environment, data["region"]]
        expected_markdown_values.extend(data[field] for field in OCID_PREFIXES)
        expected_markdown_values.extend(data["subnets"].values())
        if any(str(value) not in markdown for value in expected_markdown_values):
            fail("Markdown and JSON handoffs are inconsistent")
        if SENSITIVE_RE.search(markdown) or SENSITIVE_RE.search(args.handoff_json.read_text()):
            fail("handoff contains a prohibited sensitive pattern")
        print(
            json.dumps(
                {
                    "ok": True,
                    "project": args.project,
                    "environment": environment,
                    "target_repository": target,
                    "repository_layout": layout,
                    "handoff_path": handoff_path,
                    "json_sha256": digest(args.handoff_json),
                    "markdown_sha256": digest(args.handoff_markdown),
                },
                separators=(",", ":"),
            )
        )
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, separators=(",", ":")))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
