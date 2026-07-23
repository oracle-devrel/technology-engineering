#!/usr/bin/env python3
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
REGION_RE = re.compile(r"^[a-z]{2}-[a-z]+-[0-9]+$")
RUNTIME_CONTRACT_PATH = ".github/project-onboarding-contract.json"
OE_REVISION = "172809932c53467ab20ec6d1b44290a487211b36"


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
    return ProjectIdentity(
        project,
        match.group("environment"),
        match.group("project_name"),
    )


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
        or generator.get("release") != "v3.1.0"
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
    return (
        "config/projects.json",
        "op04_manage_project/"
        f"{identity.environment}/{identity.slug}/generated/iam.json",
    )
