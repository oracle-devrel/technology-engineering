"""Read project handoff Markdown and turn known values into form suggestions."""
import re
from typing import Any


_INVALID_VALUE_PREFIXES = (
    "<",
    "pending",
    "tbd",
    "todo",
    "n/a",
)


class HandoffService:
    """Build form suggestions from one V2 environment handoff document."""

    def __init__(self, github_client, project_name: str, environment: str):
        self.github = github_client
        self.project_name = project_name
        self.environment = environment

    @property
    def handoff_path(self) -> str:
        return f"environments/{self.environment}/environment_information.md"

    async def load_suggestions(self, template_path: str = "") -> dict[str, str]:
        content = await self.github.get_file_content(self.project_name, self.handoff_path)
        if not content:
            return {}
        references = self._extract_references(
            self._selected_cloud_content(content, template_path)
        )
        return self._build_suggestions(references, template_path=template_path)

    async def load_compartment_options(self) -> list[dict[str, str]]:
        """Return approved project compartments documented in the handoff file."""
        content = await self.github.get_file_content(self.project_name, self.handoff_path)
        if not content:
            return []
        return self._build_compartment_options(self._extract_references(content))

    @classmethod
    def _extract_references(cls, content: str) -> dict[str, str]:
        references: dict[str, str] = {}
        for line in (content or "").splitlines():
            cells = cls._parse_table_row(line)
            if len(cells) >= 2:
                reference = cells[0]
                value = cls._table_reference_value(cells)
            else:
                parsed_bullet = cls._parse_bullet_reference(line)
                if not parsed_bullet:
                    continue
                reference, value = parsed_bullet
            if cls._is_header_or_separator(reference, value):
                continue
            if not cls._is_valid_value(value):
                continue
            normalized_reference = cls._normalize_reference(reference)
            references[normalized_reference] = value
            if normalized_reference == "projects vcn" and len(cells) >= 3:
                references.setdefault("project vcn key", cells[1])
                if value.lower().startswith("ocid1."):
                    references.setdefault("project vcn ocid", value)
            cls._add_ocid_reference_alias(
                references,
                normalized_reference,
                value,
            )
        return references

    @staticmethod
    def _selected_cloud_content(content: str, template_path: str) -> str:
        """Keep Azure and GCP suggestions inside their reviewed handoff section."""
        path_parts = (template_path or "").split("/")
        cloud = path_parts[1].lower() if len(path_parts) > 1 else "oci"
        if cloud not in {"azure", "gcp"}:
            return content

        selected: list[str] = []
        active_cloud = "oci"
        for line in (content or "").splitlines():
            section = re.fullmatch(r"\s*##\s+(Azure|GCP)\s*", line, re.IGNORECASE)
            if section:
                active_cloud = section.group(1).lower()
                continue
            if active_cloud == cloud:
                selected.append(line)
        return "\n".join(selected)

    @staticmethod
    def _parse_table_row(line: str) -> list[str]:
        stripped = (line or "").strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            return []
        return [cell.strip() for cell in stripped.strip("|").split("|")]

    @staticmethod
    def _table_reference_value(cells: list[str]) -> str:
        """Use an OCID column when a handoff table includes logical keys too."""
        for cell in reversed(cells[1:]):
            if cell.strip().lower().startswith("ocid1."):
                return cell.strip()
        return cells[1]

    @staticmethod
    def _add_ocid_reference_alias(
        references: dict[str, str],
        reference: str,
        value: str,
    ) -> None:
        """Accept handoff labels such as 'DB compartment' for OCID mappings."""
        if not value.lower().startswith("ocid1."):
            return
        if reference.endswith(" compartment"):
            references.setdefault(f"{reference} ocid", value)
        if reference.endswith(" subnet"):
            references.setdefault(f"{reference} ocid", value)

    @staticmethod
    def _parse_bullet_reference(line: str) -> tuple[str, str] | None:
        match = re.fullmatch(r"\s*[-*]\s+([^:]+):\s*(.+?)\s*", line or "")
        if not match:
            return None
        return match.group(1).strip(), match.group(2).strip()

    @staticmethod
    def _is_header_or_separator(reference: str, value: str) -> bool:
        joined = f"{reference} {value}".strip().lower()
        if joined in {
            "reference default",
            "reference value",
            "convention value",
            "setting where it is configured",
        }:
            return True
        return bool(re.fullmatch(r"[-:\s]+", reference) and re.fullmatch(r"[-:\s]+", value))

    @staticmethod
    def _is_valid_value(value: str) -> bool:
        normalized = (value or "").strip()
        if not normalized:
            return False
        lowered = normalized.lower()
        return not any(lowered.startswith(prefix) for prefix in _INVALID_VALUE_PREFIXES)

    @staticmethod
    def _normalize_reference(reference: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", (reference or "").lower()).strip()

    @classmethod
    def _build_suggestions(cls, references: dict[str, str], *, template_path: str = "") -> dict[str, str]:
        suggestions: dict[str, str] = {}

        cls._set(suggestions, references, "app compartment ocid", [
            "__PROJ_APP_CMP_OCID__",
            "__PROJ_APP_OCID__",
        ])
        cls._set(suggestions, references, "db compartment ocid", [
            "__PROJ_DB_CMP_OCID__",
            "__PROJ_DB_OCID__",
        ])
        cls._set(suggestions, references, "infra compartment ocid", [
            "__PROJ_INFRA_CMP_OCID__",
            "__PROJ_INFRA_OCID__",
            "__NSG_COMPARTMENT_OCID__",
        ])
        cls._set(suggestions, references, "project parent compartment ocid", [
            "__PROJECT_PARENT_CMP_OCID__",
        ])
        project_name = (
            references.get("project key")
            or references.get("project name")
            or references.get("project key name")
            or references.get("project")
        )
        if project_name:
            suggestions["__PROJECT_NAME__"] = project_name
        cls._set(suggestions, references, "project vcn key", ["__PROJECT_VCN_KEY__"])
        cls._set(suggestions, references, "project vcn ocid", [
            "__PROJECT_VCN_OCID__",
            "__VCN_OCID__",
        ])
        cls._set(suggestions, references, "web subnet ocid", ["__PROJ_WEB_SUBNET_OCID__"])
        cls._set(suggestions, references, "app subnet ocid", [
            "__PROJ_APP_SUBNET_OCID__",
            "__VM_SUBNET_OCID__",
        ])
        cls._set(suggestions, references, "db subnet ocid", ["__PROJ_DB_SUBNET_OCID__"])
        cls._set(suggestions, references, "infra subnet ocid", ["__PROJ_INFRA_SUBNET_OCID__"])
        cls._set(suggestions, references, "compute ssh public key path", ["__DEFAULT_SSH_KEY__"])
        cls._set(suggestions, references, "google project id", [
            "__GOOGLE_PROJECT_ID__",
            "__GCP_PROJECT_ID__",
        ])
        cls._set(suggestions, references, "odb network key", ["__ODB_NETWORK_KEY__"])
        cls._set(suggestions, references, "odb network name", ["__ODB_NETWORK_KEY__"])
        cls._set(suggestions, references, "odb network resource name", ["__ODB_NETWORK_KEY__"])
        cls._set(suggestions, references, "odb network id", ["__ODB_NETWORK_ID__"])
        cls._set(suggestions, references, "client odb subnet key", ["__ODB_SUBNET_KEY__"])
        cls._set(suggestions, references, "client odb subnet name", ["__ODB_SUBNET_KEY__"])
        cls._set(suggestions, references, "client odb subnet resource name", ["__ODB_SUBNET_KEY__"])
        cls._set(suggestions, references, "client odb subnet id", ["__ODB_SUBNET_ID__"])
        cls._set(suggestions, references, "admin password secret id", ["__ADMIN_PASSWORD_SECRET_ID__"])
        cls._set(suggestions, references, "admin password secret reference", ["__ADMIN_PASSWORD_SECRET_ID__"])
        cls._set(suggestions, references, "approved password secret reference", ["__ADMIN_PASSWORD_SECRET_ID__"])
        cls._set(suggestions, references, "azure resource group", ["__RESOURCE_GROUP__"])
        cls._set(suggestions, references, "resource group", ["__RESOURCE_GROUP__"])
        cls._set(suggestions, references, "azure location", ["__AZURE_LOCATION__"])
        cls._set(suggestions, references, "azure region", ["__AZURE_LOCATION__"])
        cls._set(suggestions, references, "azure resource group", ["__AZURE_RESOURCE_GROUP_NAME__"])
        cls._set(suggestions, references, "azure subnet id", ["__AZURE_SUBNET_ID__"])
        cls._set(suggestions, references, "azure nsg id", ["__AZURE_NSG_ID__"])
        cls._set(suggestions, references, "azure adb subnet id", ["__AZURE_ADB_SUBNET_ID__"])
        cls._set(suggestions, references, "azure vnet id", ["__AZURE_VNET_ID__"])
        cls._set(suggestions, references, "google zone", ["__GOOGLE_ZONE__"])
        cls._set(suggestions, references, "google subnetwork", ["__GOOGLE_SUBNETWORK__"])
        cls._set(suggestions, references, "google service account", ["__GOOGLE_SERVICE_ACCOUNT__"])
        cls._set_region_suggestion(suggestions, references, template_path)
        cls._set_network_defaults(suggestions, template_path)
        cls._set_contextual_aliases(suggestions, references, template_path)
        cls._set_explicit_nsg_suggestions(suggestions, references)
        cls._set_nsg_pattern_suggestions(suggestions, references)
        return suggestions

    @staticmethod
    def _set(
        suggestions: dict[str, str],
        references: dict[str, str],
        reference: str,
        placeholders: list[str],
    ) -> None:
        value = references.get(reference)
        if not value:
            return
        for placeholder in placeholders:
            suggestions[placeholder] = value

    @staticmethod
    def _build_compartment_options(
        references: dict[str, str],
    ) -> list[dict[str, str]]:
        """Build a stable, de-duplicated selector from known handoff entries."""
        compartment_references = (
            ("project parent compartment ocid", "Project parent compartment"),
            ("app compartment ocid", "Application compartment"),
            ("db compartment ocid", "Database compartment"),
            ("infra compartment ocid", "Infrastructure compartment"),
        )
        options: list[dict[str, str]] = []
        seen_values: set[str] = set()
        for reference, label in compartment_references:
            value = references.get(reference)
            if not value or value in seen_values:
                continue
            seen_values.add(value)
            options.append({"value": value, "label": f"{label} ({value})"})
        return options

    @staticmethod
    def _set_contextual_aliases(
        suggestions: dict[str, str],
        references: dict[str, str],
        template_path: str,
    ) -> None:
        path = (template_path or "").lower()
        if "/compute/" in path:
            app_compartment = references.get("app compartment ocid")
            if app_compartment:
                suggestions["__COMPARTMENT_OCID__"] = app_compartment
        elif "/databases/" in path or "/database/" in path:
            db_compartment = references.get("db compartment ocid")
            if db_compartment:
                suggestions["__COMPARTMENT_OCID__"] = db_compartment
        elif not template_path:
            db_compartment = references.get("db compartment ocid")
            if db_compartment:
                suggestions["__COMPARTMENT_OCID__"] = db_compartment

    @staticmethod
    def _set_network_defaults(suggestions: dict[str, str], template_path: str) -> None:
        path = (template_path or "").lower()
        if "/network/" in path:
            suggestions["__PROJECT_NSG_CATEGORY__"] = "project-nsgs"

    @staticmethod
    def _set_region_suggestion(
        suggestions: dict[str, str],
        references: dict[str, str],
        template_path: str,
    ) -> None:
        path = (template_path or "").lower()
        if "/gcp/" in path:
            candidates = (
                "target google region",
                "google region",
                "default gcp region",
                "gcp region",
            )
            cloud_placeholder = "__GCP_REGION__"
        elif "/azure/" in path:
            candidates = ("azure region", "azure location", "default azure region")
            cloud_placeholder = "__AZURE_REGION__"
        else:
            candidates = ("primary oci region", "default oci region", "oci region")
            cloud_placeholder = "__OCI_REGION__"

        for reference in (*candidates, "target region", "default region", "region"):
            value = references.get(reference)
            if not value:
                continue
            suggestions["__REGION__"] = value
            suggestions[cloud_placeholder] = value
            return

    @staticmethod
    def _set_nsg_pattern_suggestions(suggestions: dict[str, str], references: dict[str, str]) -> None:
        key_pattern = references.get("approved nsg key pattern")
        if key_pattern:
            for tier in ("web", "app", "db", "infra"):
                suggestions.setdefault(
                    f"__NSG_{tier.upper()}_KEY__",
                    key_pattern.replace("<TIER>", tier.upper()),
                )

        display_pattern = references.get("approved nsg display name pattern")
        if display_pattern:
            for tier in ("web", "app", "db", "infra"):
                suggestions.setdefault(
                    f"__NSG_{tier.upper()}_DISPLAY_NAME__",
                    display_pattern.replace("<tier>", tier),
                )

    @classmethod
    def _set_explicit_nsg_suggestions(cls, suggestions: dict[str, str], references: dict[str, str]) -> None:
        for tier in ("web", "app", "db", "infra"):
            upper_tier = tier.upper()
            cls._set(
                suggestions,
                references,
                f"approved {tier} nsg key",
                [f"__NSG_{upper_tier}_KEY__"],
            )
            cls._set(
                suggestions,
                references,
                f"approved {tier} nsg display name",
                [f"__NSG_{upper_tier}_DISPLAY_NAME__"],
            )
