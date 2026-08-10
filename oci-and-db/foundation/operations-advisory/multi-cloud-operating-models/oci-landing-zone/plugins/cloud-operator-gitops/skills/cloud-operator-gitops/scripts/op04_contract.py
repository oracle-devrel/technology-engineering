#!/usr/bin/env python3
# Copyright (c) 2026 Oracle and/or its affiliates.
"""Small protected contract shared by the OP04 skill commands."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_RE = re.compile(
    r"^(?P<environment>dev|test|uat|prod)-"
    r"(?P<project_name>[a-z][a-z0-9]*(?:-[a-z0-9]+)*)$"
)
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REGION_RE = re.compile(r"^[a-z]{2}-[a-z]+-[0-9]+$")
RUNTIME_CONTRACT_PATH = ".github/project-onboarding-contract.json"
OE_REVISION = "dab13856ba6701c45baafc163780bb76562c039a"


class ContractError(ValueError):
    """Raised when the protected landing-zone contract is invalid."""


@dataclass(frozen=True)
class ProjectIdentity:
    slug: str
    environment: str
    project_name: str


def git_text(repo: Path, *args: str) -> str:
    result = subprocess.run(
        [
            "git",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.hooksPath=/dev/null",
            *args,
        ],
        cwd=repo,
        text=True,
        capture_output=True,
        timeout=15,
        check=False,
    )
    if result.returncode:
        raise ContractError("Git contract inspection failed.")
    return result.stdout


def load_at(repo: Path, ref: str, path: str) -> Any:
    try:
        return json.loads(git_text(repo, "show", f"{ref}:{path}"))
    except (ContractError, json.JSONDecodeError) as exc:
        raise ContractError("The protected onboarding contract is invalid.") from exc


def validate_project(project: str) -> ProjectIdentity:
    match = PROJECT_RE.fullmatch(project)
    if match is None or len(match.group("project_name")) > 30:
        raise ContractError("The project must match <environment>-<dns-name>.")
    environment = match.group("environment")
    project_name = match.group("project_name")
    repository_prefix = "prod-" if environment == "prod" else "nonprod-"
    if project_name.startswith(repository_prefix):
        raise ContractError(
            "The project DNS name must not repeat the derived repository "
            f"prefix {repository_prefix}."
        )
    return ProjectIdentity(
        project,
        environment,
        project_name,
    )


def canonical_onboarding_branch(project: str, base_sha: str) -> str:
    """Return the only branch that may carry a new OP04 onboarding change."""
    identity = validate_project(project)
    if SHA_RE.fullmatch(base_sha) is None:
        raise ContractError("The onboarding base revision is invalid.")
    return f"agent/project-onboard-{identity.slug}-{base_sha[:12]}"


def validate_runtime_contract(
    repo: Path,
    ref: str,
    environment: str,
) -> dict[str, Any]:
    contract = load_at(repo, ref, RUNTIME_CONTRACT_PATH)
    allowed = ["dev", "test", "uat", "prod"]
    generator = contract.get("op04_generator", {})
    if (
        contract.get("contract_version") != 3
        or contract.get("allowed_environments") != allowed
        or environment not in allowed
        or contract.get("project_catalog") != "config/projects.json"
        or generator.get("repository")
        != "oci-landing-zones/oci-landing-zone-operating-entities"
        or generator.get("release") != "master"
        or generator.get("revision") != OE_REVISION
        or generator.get("adapter") != "config/render.libsonnet"
    ):
        raise ContractError(
            f"The landing-zone runtime does not support governed "
            f"{environment} onboarding."
        )
    blueprint = load_at(
        repo,
        ref,
        contract["environment_blueprints"][environment],
    )
    if (
        blueprint.get("schema_version") != 2
        or blueprint.get("environment") != environment
        or REGION_RE.fullmatch(str(blueprint.get("region", ""))) is None
    ):
        raise ContractError("The protected environment blueprint is invalid.")
    return contract


def expected_paths(project: str) -> tuple[str, str]:
    identity = validate_project(project)
    root = (
        "op04_manage_project/"
        f"{identity.environment}/{identity.slug}/generated"
    )
    return (
        "config/projects.json",
        f"{root}/iam.json",
    )
