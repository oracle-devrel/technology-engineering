#!/usr/bin/env python3
# Copyright (c) 2026 Oracle and/or its affiliates.
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
ORG_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SECURITY_PROFILE = "repository-secrets"
LAYOUT_ENVIRONMENTS = {
    "shared-nonprod-v2": ("dev", "test", "uat"),
    "production": ("prod",),
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
    template_repository: str
    template_revision: str
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
    all_owner_keys = {"platform", "dev", "test", "uat", "prod"}
    selected_keys = {"platform", *environments}
    if not isinstance(value, dict) or set(value) != all_owner_keys:
        raise RepositoryContractError("CODEOWNERS mapping is incomplete.")
    result: dict[str, tuple[str, ...]] = {}
    for key in sorted(selected_keys):
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
    installation_file: Path,
    handoff_json: Path,
    project: str,
) -> RepositoryInitialization:
    try:
        identity = validate_project(project)
    except ContractError as exc:
        raise RepositoryContractError(str(exc)) from exc
    installation = load_json(installation_file)
    handoff = load_json(handoff_json)
    customer_org = installation.get("customer_org")
    foundation = installation.get("foundation")
    project_templates = installation.get("project_templates")
    if (
        installation.get("schema_version") != 3
        or not isinstance(customer_org, str)
        or ORG_RE.fullmatch(customer_org) is None
        or not isinstance(foundation, dict)
        or set(foundation) != {"repository", "branch"}
        or not isinstance(foundation.get("repository"), str)
        or REPOSITORY_RE.fullmatch(foundation["repository"]) is None
        or not foundation["repository"].startswith(f"{customer_org}/")
        or foundation.get("branch") != "main"
        or not isinstance(project_templates, dict)
        or set(project_templates) != {"shared_nonprod_v2", "production"}
        or any(
            not isinstance(template, dict)
            or set(template) != {"repository", "revision"}
            or not isinstance(template.get("repository"), str)
            or REPOSITORY_RE.fullmatch(template["repository"]) is None
            or not template["repository"].startswith(f"{customer_org}/")
            or not isinstance(template.get("revision"), str)
            or SHA_RE.fullmatch(template["revision"]) is None
            for template in project_templates.values()
        )
    ):
        raise RepositoryContractError(
            "The Cloud Operator installation does not support project initialization."
        )
    environment_contracts = installation.get("environments")
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
        "production"
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
        handoff.get("schema_version") != 3
        or handoff.get("environment") != identity.environment
        or handoff.get("target_repository") != target_repository
        or handoff.get("project_slug") != target_repository
        or handoff.get("repository_layout") != layout
        or handoff.get("handoff_path") != handoff_path
        or handoff.get("source_repository") != foundation["repository"]
        or not all(
            isinstance(handoff.get(field), str)
            and handoff[field].startswith("ocid1.compartment.")
            for field in (
                "project_root_compartment",
                "app_compartment",
                "database_compartment",
                "infrastructure_compartment",
            )
        )
        or len(
            {
                handoff.get("project_root_compartment"),
                handoff.get("app_compartment"),
                handoff.get("database_compartment"),
                handoff.get("infrastructure_compartment"),
            }
        ) != 4
    ):
        raise RepositoryContractError(
            "The handoff does not match the selected project repository."
        )
    template_key = "production" if layout == "production" else "shared_nonprod_v2"
    template = project_templates[template_key]
    template_repository = template["repository"]
    template_revision = template["revision"]
    owners = validate_owner_map(layout, installation.get("codeowners"))
    return RepositoryInitialization(
        identity=identity,
        customer_org=customer_org,
        target_repository=target_repository,
        template_repository=template_repository,
        template_revision=template_revision,
        repository_layout=layout,
        security_profile=SECURITY_PROFILE,
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
