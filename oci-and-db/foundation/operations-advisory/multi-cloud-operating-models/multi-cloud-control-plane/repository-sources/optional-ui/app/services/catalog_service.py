"""Catalog service for gitops-templates path matching and JSON loading."""
import json
import logging
import math
import re
from pathlib import PurePosixPath
from typing import Any

from pathspec import PathSpec
from pydantic import BaseModel, ValidationError

from app.schemas import OperationCatalogEntry

logger = logging.getLogger(__name__)


class JsonTemplate(BaseModel):
    """A JSON template loaded from gitops-templates."""

    path: str
    filename: str
    cloud: str
    content: dict[str, Any]


class ResourceCatalogEntry(BaseModel):
    """Resource template metadata for the resources catalog view."""

    id: str
    name: str
    cloud: str
    category: str


class CatalogService:
    """Shared service to discover and load gitops-templates content."""

    OPERATIONS_INCLUDE = PathSpec.from_lines(
        "gitignore",
        ["operations-catalog/*.json", "operations-catalog/**/*.json"],
    )
    RESOURCES_INCLUDE = PathSpec.from_lines(
        "gitignore",
        ["resources-catalog/*.json", "resources-catalog/**/*.json"],
    )
    RESOURCES_EXCLUDE = PathSpec.from_lines(
        "gitignore",
        [
            "resources-catalog/schemas/**",
            "resources-catalog/**/project-onboarding/**",
            "*onboarding*.json",
            "*credentials*.json",
            "*iam*.json",
            "*policy*.json",
        ],
    )

    def __init__(
        self,
        github_client,
        repo_name: str = "gitops-templates",
        revision: str = "main",
    ):
        self.github = github_client
        self.repo_name = repo_name
        self.revision = revision

    async def _tree_paths(self) -> list[str]:
        if self.repo_name == "gitops-templates" and hasattr(self.github, "get_repo_tree_strict"):
            tree = await self.github.get_repo_tree_strict(self.repo_name, ref=self.revision)
        else:
            tree = await self.github.get_repo_tree(self.repo_name, ref=self.revision)
        return [
            item["path"]
            for item in tree.get("tree", [])
            if isinstance(item, dict) and isinstance(item.get("path"), str)
        ]

    @staticmethod
    def _parse_path(path: str) -> tuple[str, str]:
        parsed = PurePosixPath(path)
        parts = parsed.parts
        cloud = parts[1] if len(parts) >= 2 else ""
        return parsed.name, cloud

    @staticmethod
    def _humanize_template_name(filename: str) -> str:
        special_names = {
            "project_google_adbs_template.json": "Google ADB-S",
            "project_nsgs_template.json": "Project NSGs",
        }
        if filename in special_names:
            return special_names[filename]

        name = filename.replace(".json", "")
        name = name.replace(".auto.tfvars", "")
        name = name.replace("_template", "")
        name = name.replace("project_", "")
        name = re.sub(r"[-_\.]+", " ", name).strip().title()
        for acronym in ("ADB", "BYOL", "OCI", "NSG", "VM"):
            name = re.sub(rf"\b{acronym}\b", acronym, name, flags=re.IGNORECASE)
        return re.sub(r"\bmtls\b", "mTLS", name, flags=re.IGNORECASE)

    @staticmethod
    def resource_facts(template: JsonTemplate | dict[str, Any]) -> list[str]:
        """Display unambiguous catalog or selected-record literals without inferring capacity."""
        fields = (("ecpu_count", "ECPU"), ("ocpus", "OCPU"), ("cpu_core_count", "OCPU"), ("memory_in_gbs", "GB RAM"),
                  ("non_dw_storage_size_in_gbs", "GB storage"), ("data_storage_size_in_tbs", "TB storage"),
                  ("boot_volume_size_in_gbs", "GB boot"))
        values = {field: set() for field, _ in fields}
        licenses = set()

        def collect(value, parent=""):
            if isinstance(value, dict):
                for key, child in value.items():
                    field = {"flex_shape_settings": {"memory": "memory_in_gbs"},
                             "boot_volume": {"size": "boot_volume_size_in_gbs"}}.get(parent, {}).get(key, key)
                    if key == "compute_count" and value.get("compute_model") == "ECPU":
                        field = "ecpu_count"
                    if field in values:
                        number = child if type(child) in (int, float) else (
                            float(child) if isinstance(child, str) and re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", child) else None)
                        values[field].add(number if number is not None and math.isfinite(number) else None)
                    if key == "license_model" and isinstance(child, str):
                        licenses.add({"BringYourOwnLicense": "BRING_YOUR_OWN_LICENSE",
                                      "LicenseIncluded": "LICENSE_INCLUDED"}.get(child, child))
                    collect(child, key)
            elif isinstance(value, list):
                for child in value:
                    collect(child, parent)

        collect(template.content if isinstance(template, JsonTemplate) else template)
        facts = [f"{next(iter(values[field])):g} {unit}" for field, unit in fields
                 if len(values[field]) == 1 and None not in values[field]]
        if licenses == {"BRING_YOUR_OWN_LICENSE"}:
            facts.append("BYOL")
        elif licenses == {"LICENSE_INCLUDED"}:
            facts.append("License included")
        return facts

    @classmethod
    def humanize_template_name(cls, filename: str) -> str:
        """Humanize template filenames for UI labels."""
        return cls._humanize_template_name(filename)

    @staticmethod
    def public_adb_notice(data: dict[str, Any]) -> str:
        """Describe public Azure ADB exposure before submission and review."""
        databases = data.get("oracle_autonomous_databases", {})
        if isinstance(databases, dict) and any(
            isinstance(adb, dict) and adb.get("network_access") == "public"
            for adb in databases.values()
        ):
            return (
                "This manifest includes a public Azure ADB endpoint that allows "
                "connections from any IP address. A client wallet (mTLS) and "
                "database authentication are required."
            )
        return ""

    @staticmethod
    def _resource_category(path: str) -> str:
        parts = PurePosixPath(path).parts
        if len(parts) >= 3:
            if parts[1] == "oci" and parts[2] == "network":
                return "Project NSGs"
            category = parts[2].replace("-", " ").replace("_", " ")
            return category.title()
        return "Resource"

    async def _match_paths(self, include: PathSpec, exclude: PathSpec | None = None) -> list[str]:
        paths = await self._tree_paths()
        matched = list(include.match_files(paths))
        if exclude:
            matched = [path for path in matched if not exclude.match_file(path)]
        return sorted(set(matched))

    async def load_json_template(self, path: str) -> JsonTemplate | None:
        content = await self.github.get_file_content(self.repo_name, path, ref=self.revision)
        if not content:
            return None
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            logger.warning("Invalid JSON in %s: %s", path, exc)
            return None
        if not isinstance(parsed, dict):
            logger.warning("Skipping non-object JSON template: %s", path)
            return None
        filename, cloud = self._parse_path(path)
        return JsonTemplate(path=path, filename=filename, cloud=cloud, content=parsed)

    async def _load_templates(self, paths: list[str]) -> list[JsonTemplate]:
        templates: list[JsonTemplate] = []
        for path in paths:
            template = await self.load_json_template(path)
            if template:
                templates.append(template)
        return templates

    async def list_operations_catalog(self, cloud_filter: str | None = None) -> list[OperationCatalogEntry]:
        templates = await self._load_templates(await self._match_paths(self.OPERATIONS_INCLUDE))
        operations: list[OperationCatalogEntry] = []
        for template in templates:
            cloud = template.cloud
            if cloud_filter and cloud != cloud_filter:
                continue
            operation_id = template.filename.replace(".json", "")
            payload = dict(template.content)
            payload["id"] = operation_id
            payload["cloud"] = cloud
            try:
                operations.append(OperationCatalogEntry.model_validate(payload))
            except ValidationError as exc:
                logger.warning("Invalid operation catalog entry %s: %s", template.path, exc)
        return operations

    async def list_resources_catalog_entries(self) -> list[ResourceCatalogEntry]:
        paths = await self._match_paths(self.RESOURCES_INCLUDE, exclude=self.RESOURCES_EXCLUDE)
        entries: list[ResourceCatalogEntry] = []
        for path in paths:
            filename, cloud = self._parse_path(path)
            entries.append(
                ResourceCatalogEntry(
                    id=path,
                    name=self.humanize_template_name(filename),
                    cloud=cloud,
                    category=self._resource_category(path),
                )
            )
        return entries
