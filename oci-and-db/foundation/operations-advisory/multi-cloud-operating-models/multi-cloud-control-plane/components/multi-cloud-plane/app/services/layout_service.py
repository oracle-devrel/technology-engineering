"""Explicit validation for shared non-production project repositories."""
from __future__ import annotations

import json


class LayoutError(ValueError):
    """The protected project layout contract is absent or invalid."""


class LayoutService:
    SHARED = "shared-nonprod-v2"
    ALLOWED_ENVIRONMENTS = frozenset({"dev", "test", "uat"})

    def __init__(self, github_client, project_name: str):
        self.github, self.project_name = github_client, project_name

    async def load(self) -> dict:
        content = await self.github.get_file_content(self.project_name, "control-plane.json")
        if not content:
            raise LayoutError("The protected shared layout contract is missing")
        try:
            contract = json.loads(content)
        except json.JSONDecodeError as exc:
            raise LayoutError("Invalid control-plane.json") from exc
        if contract.get("repository_layout") != self.SHARED:
            raise LayoutError("Unsupported repository layout")
        if contract.get("target_repository") != self.project_name:
            raise LayoutError("Repository does not match its protected layout contract")
        return contract

    @classmethod
    def handoff_path(cls, layout: dict, environment: str | None = None) -> str:
        if environment not in cls.ALLOWED_ENVIRONMENTS:
            raise LayoutError("An allowed shared non-production environment is required")
        config = (layout.get("environments") or {}).get(environment) or {}
        path = config.get("handoff_path")
        if path != f"environments/{environment}/environment_information.md":
            raise LayoutError("Shared environment handoff path is invalid")
        return path

    @classmethod
    def manifest_prefix(cls, layout: dict, cloud: str, region: str, environment: str | None = None) -> str:
        cls.handoff_path(layout, environment)
        return f"{cloud}/{environment}/{region}"
