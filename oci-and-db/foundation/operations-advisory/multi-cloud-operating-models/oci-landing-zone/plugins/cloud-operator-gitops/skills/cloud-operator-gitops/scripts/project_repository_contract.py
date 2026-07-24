#!/usr/bin/env python3
"""Protected project-repository initialization contract."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from op04_contract import (
    ContractError,
    ProjectIdentity,
    validate_project,
)


SHA_RE = re.compile(r"^[0-9a-f]{40}$")
OWNER_RE = re.compile(
    r"^@[A-Za-z0-9][A-Za-z0-9-]{0,38}"
    r"(?:/[A-Za-z0-9][A-Za-z0-9_.-]{0,99})?$"
)
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
ORG_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
SECURITY_PROFILES = {"github-environments", "repository-secrets"}
LAYOUT_ENVIRONMENTS = {
    "shared-nonprod-v2": ("dev", "test", "uat"),
    "production-v1": ("prod",),
}
CODEOWNER_TOKENS = {
    "platform": "__PLATFORM_OWNERS__",
    "dev": "__DEV_OWNERS__",
    "test": "__TEST_OWNERS__",
    "uat": "__UAT_OWNERS__",
    "prod": "__PROD_OWNERS__",
}
PLACEHOLDER_RE = re.compile(r"__[A-Z0-9_]+__")


class RepositoryContractError(ValueError):
    """Raised when project repository initialization is unsafe."""


@dataclass(frozen=True)
class RepositoryInitialization:
    identity: ProjectIdentity
    customer_org: str
    target_repository: str
    repository_layout: str
    security_profile: str
    handoff_path: str
    codeowners: dict[str, tuple[str, ...]]
    handoff: dict[str, Any]


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RepositoryContractError(
            f"Invalid JSON contract: {path.name}."
        ) from exc
    if not isinstance(value, dict):
        raise RepositoryContractError(
            f"Invalid JSON contract: {path.name}."
        )
    return value


def git(repo: Path, *args: str) -> str:
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
        raise RepositoryContractError("Git repository inspection failed.")
    return result.stdout


def validate_owner_map(
    layout: str,
    value: Any,
) -> dict[str, tuple[str, ...]]:
    environments = LAYOUT_ENVIRONMENTS[layout]
    expected_keys = {"platform", *environments}
    if not isinstance(value, dict) or set(value) != expected_keys:
        raise RepositoryContractError("CODEOWNERS mapping is incomplete.")
    result: dict[str, tuple[str, ...]] = {}
    for key in sorted(expected_keys):
        owners = value[key]
        if (
            not isinstance(owners, list)
            or not owners
            or any(
                not isinstance(owner, str)
                or OWNER_RE.fullmatch(owner) is None
                for owner in owners
            )
            or len(owners) != len(set(owners))
        ):
            raise RepositoryContractError(
                f"CODEOWNERS mapping is invalid for {key}."
            )
        result[key] = tuple(owners)
    return result


def load_initialization(
    deployment_contract: Path,
    handoff_json: Path,
    project: str,
) -> RepositoryInitialization:
    try:
        identity = validate_project(project)
    except ContractError as exc:
        raise RepositoryContractError(str(exc)) from exc
    contract = load_json(deployment_contract)
    handoff = load_json(handoff_json)
    customer_org = contract.get("customer_org")
    project_state_bucket = contract.get("project_state_bucket")
    project_templates = contract.get("project_templates")
    if (
        contract.get("schema_version") != 1
        or not isinstance(customer_org, str)
        or ORG_RE.fullmatch(customer_org) is None
        or REPOSITORY_RE.fullmatch(
            str(contract.get("foundation_repository", ""))
        ) is None
        or not str(
            contract.get("foundation_repository", "")
        ).startswith(f"{customer_org}/")
        or SHA_RE.fullmatch(str(contract.get("foundation_ref", ""))) is None
        or not isinstance(project_state_bucket, str)
        or not project_state_bucket.strip()
        or project_state_bucket != project_state_bucket.strip()
        or PLACEHOLDER_RE.search(project_state_bucket) is not None
        or not isinstance(project_templates, dict)
        or set(project_templates)
        != {"shared-nonprod-v2", "production-v1"}
        or any(
            not isinstance(value, dict)
            or not str(value.get("repository", "")).startswith(
                f"{customer_org}/"
            )
            or SHA_RE.fullmatch(str(value.get("revision", ""))) is None
            for value in project_templates.values()
        )
        or contract.get("target_repository_prefixes")
        != {
            "dev": "nonprod",
            "test": "nonprod",
            "uat": "nonprod",
            "prod": "prod",
        }
        or contract.get("handoff_path_template")
        != "environments/{environment}/environment_information.md"
    ):
        raise RepositoryContractError(
            "The deployment contract does not support project initialization."
        )
    environment_contracts = contract.get("environments")
    if (
        not isinstance(environment_contracts, list)
        or not any(
            isinstance(item, dict)
            and item.get("name") == identity.environment
            and item.get("region") == handoff.get("region")
            for item in environment_contracts
        )
    ):
        raise RepositoryContractError(
            "The selected environment is not configured."
        )
    layout = (
        "production-v1"
        if identity.environment == "prod"
        else "shared-nonprod-v2"
    )
    prefix = "prod" if identity.environment == "prod" else "nonprod"
    target_repository = f"{prefix}-{identity.project_name}"
    handoff_path = (
        f"environments/{identity.environment}/"
        "environment_information.md"
    )
    if (
        handoff.get("schema_version") != 2
        or handoff.get("environment") != identity.environment
        or handoff.get("target_repository") != target_repository
        or handoff.get("project_slug") != target_repository
        or handoff.get("repository_layout") != layout
        or handoff.get("handoff_path") != handoff_path
    ):
        raise RepositoryContractError(
            "The handoff does not match the selected project repository."
        )
    templates = project_templates
    if (
        not isinstance(templates, dict)
        or layout not in templates
        or not isinstance(templates[layout], dict)
        or templates[layout].get("repository")
        != f"{customer_org}/"
        f"{'prod' if layout == 'production-v1' else 'nonprod'}"
        "-project-template"
        or SHA_RE.fullmatch(
            str(templates[layout].get("revision", ""))
        ) is None
    ):
        raise RepositoryContractError(
            "The pinned project template contract is invalid."
        )
    initialization = contract.get("project_repository_initialization")
    selected = (
        initialization.get(layout)
        if isinstance(initialization, dict)
        else None
    )
    if (
        not isinstance(selected, dict)
        or selected.get("security_profile") not in SECURITY_PROFILES
    ):
        raise RepositoryContractError(
            "The project security profile is invalid."
        )
    owners = validate_owner_map(layout, selected.get("codeowners"))
    return RepositoryInitialization(
        identity=identity,
        customer_org=customer_org,
        target_repository=target_repository,
        repository_layout=layout,
        security_profile=selected["security_profile"],
        handoff_path=handoff_path,
        codeowners=owners,
        handoff=handoff,
    )


def validate_origin(
    repo: Path,
    initialization: RepositoryInitialization,
) -> None:
    expected = (
        f"{initialization.customer_org}/"
        f"{initialization.target_repository}"
    )
    remote = git(repo, "remote", "get-url", "origin").strip()
    accepted = {
        f"https://github.com/{expected}",
        f"https://github.com/{expected}.git",
        f"git@github.com:{expected}.git",
        f"ssh://git@github.com/{expected}.git",
    }
    if remote not in accepted:
        raise RepositoryContractError(
            "The Git remote does not match the handoff target repository."
        )


def render_codeowners(
    template: str,
    initialization: RepositoryInitialization,
) -> str:
    result = template
    for key, token in CODEOWNER_TOKENS.items():
        if token in result:
            owners = initialization.codeowners.get(key)
            if owners is None:
                raise RepositoryContractError(
                    f"Unexpected CODEOWNERS token: {token}."
                )
            result = result.replace(token, " ".join(owners))
    if re.search(r"__[A-Z0-9_]+__", result):
        raise RepositoryContractError(
            "An unresolved CODEOWNERS placeholder remains."
        )
    return result


def validate_template_placeholders(
    repo: Path,
    initialization: RepositoryInitialization,
) -> None:
    allowed = {
        "control-plane.json": {"__PROJECT__"},
        ".github/CODEOWNERS.template": {
            CODEOWNER_TOKENS["platform"],
            *(
                CODEOWNER_TOKENS[environment]
                for environment in LAYOUT_ENVIRONMENTS[
                    initialization.repository_layout
                ]
            ),
        },
    }
    for relative in git(repo, "ls-files").splitlines():
        path = repo / relative
        if not path.is_file():
            raise RepositoryContractError(
                f"Invalid template path: {relative}."
            )
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        placeholders = set(PLACEHOLDER_RE.findall(text))
        if placeholders != allowed.get(relative, set()):
            raise RepositoryContractError(
                f"Unexpected template placeholder in {relative}."
            )


def validate_no_placeholders(repo: Path) -> None:
    for relative in git(
        repo,
        "ls-files",
        "--cached",
        "--others",
        "--exclude-standard",
    ).splitlines():
        path = repo / relative
        if not path.exists():
            continue
        if not path.is_file():
            raise RepositoryContractError(
                f"Invalid initialized path: {relative}."
            )
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if PLACEHOLDER_RE.search(text):
            raise RepositoryContractError(
                f"Unresolved repository placeholder in {relative}."
            )
