"""GitHub repository identity parsing."""

from __future__ import annotations

import re

from .common import ORG_RE, PROJECT_PATTERN, failure


def parse_origin(value: str) -> tuple[str, str]:
    """Extract the organization and governed project from a GitHub origin."""
    organization_pattern = ORG_RE.pattern[1:-1]
    project_pattern = PROJECT_PATTERN.pattern[1:-1]
    for prefix in (r"https://github\.com/", r"git@github\.com:", r"ssh://git@github\.com/"):
        match = re.fullmatch(
            rf"{prefix}(?P<organization>{organization_pattern})/"
            rf"(?P<project>{project_pattern})(?:\.git)?",
            value,
        )
        if match is not None:
            return match.group("organization"), match.group("project")
    failure("INVALID_ORIGIN", "The origin repository is not allowed.")
