"""Project repository and environment boundaries."""
from __future__ import annotations

import re
from dataclasses import dataclass


_PROJECT_RE = re.compile(r"^[a-z][a-z0-9-]{0,62}$")
_NONPROD_ENVIRONMENTS = ("dev", "test", "uat")


class ProjectContextError(ValueError):
    """Raised when a project repository and environment do not agree."""


@dataclass(frozen=True)
class ProjectContext:
    """A project repository and its fixed environment boundary."""

    repository: str
    layout: str
    environment: str
    handoff_path: str


def project_context(repository: str, environment: str) -> ProjectContext:
    """Return a project boundary only when repository and environment agree."""
    project_repository = (repository or "").strip()
    selected_environment = (environment or "").strip().lower()
    if project_repository.startswith("nonprod-"):
        project = project_repository.removeprefix("nonprod-")
        if _PROJECT_RE.fullmatch(project) and selected_environment in _NONPROD_ENVIRONMENTS:
            return ProjectContext(
                repository=project_repository,
                layout="nonproduction",
                environment=selected_environment,
                handoff_path=f"environments/{selected_environment}/environment_information.md",
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
    raise ProjectContextError("project repository and environment do not match")


def environment_options(repository: str) -> list[str]:
    """Return the allowed environments for a governed project repository."""
    if (repository or "").strip().startswith("prod-"):
        return [project_context(repository, "prod").environment]
    project_context(repository, "dev")
    return list(_NONPROD_ENVIRONMENTS)
