"""Fail-closed loading for an installed MCCP deployment contract."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


_ORG_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
_PROJECT_RE = re.compile(r"^[a-z][a-z0-9-]{0,62}$")
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_PLACEHOLDER_RE = re.compile(r"__[A-Z0-9_]+__")
_NONPROD_ENVIRONMENTS = frozenset({"dev", "test", "uat"})


class ContractError(ValueError):
    """Raised when an installed deployment contract is unsafe to use."""


@dataclass(frozen=True)
class ProjectContext:
    """A project repository and its permitted environment boundary."""

    repository: str
    layout: str
    environment: str
    handoff_path: str


@dataclass(frozen=True)
class DeploymentContract:
    """The subset of the rendered schema V3 contract used by the UI."""

    customer_org: str
    catalog_repository: str
    catalog_revision: str
    nonprod_environments: frozenset[str]

    @classmethod
    def load(cls, path: str | Path) -> "DeploymentContract":
        """Load and validate a fully rendered installation contract."""
        contract_path = Path(path)
        try:
            raw = contract_path.read_text(encoding="utf-8")
            payload = json.loads(raw)
        except (OSError, json.JSONDecodeError) as exc:
            raise ContractError("deployment contract cannot be read") from exc
        if not isinstance(payload, dict):
            raise ContractError("deployment contract must be a JSON object")
        if _PLACEHOLDER_RE.search(raw):
            raise ContractError("deployment contract contains an unresolved placeholder")
        if payload.get("schema_version") != 3:
            raise ContractError("deployment contract must use schema version 3")

        customer_org = payload.get("customer_org")
        if not isinstance(customer_org, str) or not _ORG_RE.fullmatch(customer_org):
            raise ContractError("deployment contract has an invalid customer organization")

        repositories = payload.get("core_repositories")
        catalogs = repositories.get("catalogs") if isinstance(repositories, dict) else None
        if not isinstance(catalogs, dict):
            raise ContractError("deployment contract has no catalog repository")
        catalog_repository = catalogs.get("repository")
        expected_catalog_repository = f"{customer_org}/gitops-templates"
        if catalog_repository != expected_catalog_repository:
            raise ContractError("deployment contract catalog repository is not customer-owned")
        catalog_revision = catalogs.get("revision")
        if not isinstance(catalog_revision, str) or not _SHA_RE.fullmatch(catalog_revision):
            raise ContractError("deployment contract requires an immutable catalog revision")

        layout = payload.get("repository_layout")
        if not isinstance(layout, dict) or layout.get("repository_pattern") != "nonprod-<project>":
            raise ContractError("deployment contract has an invalid non-production layout")
        environments = layout.get("environment_allowlist")
        if not isinstance(environments, list) or set(environments) != _NONPROD_ENVIRONMENTS:
            raise ContractError("deployment contract has an invalid non-production environment allowlist")
        if layout.get("handoff_path") != "environments/<environment>/environment_information.md":
            raise ContractError("deployment contract has an invalid non-production handoff path")

        production_layout = payload.get("production_layout")
        if (
            not isinstance(production_layout, dict)
            or production_layout.get("repository_pattern") != "prod-<project>"
            or production_layout.get("handoff_path")
            != "environments/prod/environment_information.md"
        ):
            raise ContractError("deployment contract has an invalid production layout")

        return cls(
            customer_org=customer_org,
            catalog_repository=catalog_repository,
            catalog_revision=catalog_revision,
            nonprod_environments=frozenset(environments),
        )

    def project_context(self, repository: str, environment: str) -> ProjectContext:
        """Return a project boundary only when repository and environment agree."""
        project_repository = (repository or "").strip()
        selected_environment = (environment or "").strip().lower()
        if project_repository.startswith("nonprod-"):
            project = project_repository.removeprefix("nonprod-")
            if _PROJECT_RE.fullmatch(project) and selected_environment in self.nonprod_environments:
                return ProjectContext(
                    repository=project_repository,
                    layout="nonproduction",
                    environment=selected_environment,
                    handoff_path=(
                        f"environments/{selected_environment}/environment_information.md"
                    ),
                )
        elif project_repository.startswith("prod-"):
            project = project_repository.removeprefix("prod-")
            if _PROJECT_RE.fullmatch(project) and selected_environment == "prod":
                return ProjectContext(
                    repository=project_repository,
                    layout="production",
                    environment="prod",
                    handoff_path="environments/prod/environment_information.md",
                )
        raise ContractError("project repository and environment do not match the deployment contract")


def load_installed_contract(path: str | Path) -> DeploymentContract:
    """Load the rendered contract used by this UI installation."""
    return DeploymentContract.load(path)
