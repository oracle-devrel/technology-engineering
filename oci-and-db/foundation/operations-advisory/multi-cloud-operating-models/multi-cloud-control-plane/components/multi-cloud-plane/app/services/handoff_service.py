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
    """Build form suggestions from a caller-resolved environment handoff."""

    def __init__(self, github_client, project_name: str):
        self.github = github_client
        self.project_name = project_name

    async def load_suggestions(self, handoff_path: str, template_path: str = "") -> dict[str, str]:
        """Load the caller-resolved handoff; shared paths are never inferred."""
        content = await self.github.get_file_content(self.project_name, handoff_path)
        if not content:
            return {}
        references = self._extract_references(content)
        return self._build_suggestions(references, template_path=template_path)

    @classmethod
    def _extract_references(cls, content: str) -> dict[str, str]:
        references: dict[str, str] = {}
        for line in (content or "").splitlines():
            cells = cls._parse_table_row(line)
            if len(cells) >= 2:
                reference, value = cells[0], cells[1]
            else:
                parsed_bullet = cls._parse_bullet_reference(line)
                if not parsed_bullet:
                    continue
                reference, value = parsed_bullet
            if cls._is_header_or_separator(reference, value):
                continue
            if not cls._is_valid_value(value):
                continue
            references[cls._normalize_reference(reference)] = value
        return references

    @staticmethod
    def _parse_table_row(line: str) -> list[str]:
        stripped = (line or "").strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            return []
        return [cell.strip() for cell in stripped.strip("|").split("|")]

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
        ])
        cls._set(suggestions, references, "project parent compartment ocid", [
            "__PROJECT_PARENT_CMP_OCID__",
        ])
        cls._set(suggestions, references, "project key", ["__PROJECT_NAME__"])
        cls._set(suggestions, references, "project name", ["__PROJECT_NAME__"])
        cls._set(suggestions, references, "project key name", ["__PROJECT_NAME__"])
        cls._set(suggestions, references, "project vcn key", ["__PROJECT_VCN_KEY__"])
        cls._set(suggestions, references, "project vcn ocid", [
            "__PROJECT_VCN_OCID__",
            "__VCN_OCID__",
        ])
        cls._set(suggestions, references, "web subnet ocid", ["__PROJ_WEB_SUBNET_OCID__"])
        cls._set(suggestions, references, "app subnet ocid", ["__PROJ_APP_SUBNET_OCID__"])
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
