"""Fail-closed loading for the small MCCP installation configuration."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


_ORG_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
_PROJECT_RE = re.compile(r"^[a-z][a-z0-9-]{0,62}$")
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_PLACEHOLDER_RE = re.compile(r"__[A-Z0-9_]+__")
_NONPROD_ENVIRONMENTS = frozenset({"dev", "test", "uat"})


class InstallationError(ValueError):
    """Raised when an MCCP installation configuration is unsafe to use."""


@dataclass(frozen=True)
class ProjectContext:
    """A project repository and its fixed V2 environment boundary."""

    repository: str
    layout: str
    environment: str
    handoff_path: str


@dataclass(frozen=True)
class MCCPInstallation:
    """The small installation-specific configuration used by the UI."""

    customer_org: str
    catalog_repository: str
    catalog_revision: str
    nonprod_environments: frozenset[str] = _NONPROD_ENVIRONMENTS

    @classmethod
    def load(cls, path: str | Path) -> "MCCPInstallation":
        """Load and validate a fully rendered MCCP installation file."""
        installation_path = Path(path)
        try:
            raw = installation_path.read_text(encoding="utf-8")
            payload = json.loads(raw)
        except (OSError, json.JSONDecodeError) as exc:
            raise InstallationError("MCCP installation configuration cannot be read") from exc
        if not isinstance(payload, dict):
            raise InstallationError("MCCP installation configuration must be a JSON object")
        if _PLACEHOLDER_RE.search(raw):
            raise InstallationError("MCCP installation configuration contains an unresolved placeholder")
        if payload.get("schema_version") != 1:
            raise InstallationError("MCCP installation configuration must use schema version 1")

        customer_org = payload.get("customer_org")
        if not isinstance(customer_org, str) or not _ORG_RE.fullmatch(customer_org):
            raise InstallationError("MCCP installation configuration has an invalid customer organization")

        catalog_revision = payload.get("catalog_revision")
        if not isinstance(catalog_revision, str) or not _SHA_RE.fullmatch(catalog_revision):
            raise InstallationError("MCCP installation requires an immutable catalog revision")

        return cls(
            customer_org=customer_org,
            catalog_repository=f"{customer_org}/gitops-templates",
            catalog_revision=catalog_revision,
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
        raise InstallationError("project repository and environment do not match the MCCP installation")


def load_mccp_installation(path: str | Path) -> MCCPInstallation:
    """Load the rendered MCCP installation used by this UI instance."""
    return MCCPInstallation.load(path)
