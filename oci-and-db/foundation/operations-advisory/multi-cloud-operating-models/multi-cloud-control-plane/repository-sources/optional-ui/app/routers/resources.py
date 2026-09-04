"""Resources HTMX partials - resource management and deployment."""
from copy import deepcopy
import json
import logging
import re
from html import escape
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, StringConstraints, ValidationError

from app.auth import (
    ProjectRead,
    ProjectSelected,
    ensure_project_write_access,
    require_github_client,
)
from app.config import settings
from app.github import GitHubClient, github_client as default_github_client
from app.forms import (
    htmx_error_context,
    request_form_payload,
    validation_messages,
)
from app.helpers import (
    extract_form_fields,
    fill_template_with_missing,
    find_raw_placeholders,
    render_partial,
    render_repository_state_error,
)
from app.services.catalog_service import CatalogService
from app.services.installation_service import load_mccp_installation
from app.services.dashboard_service import DashboardService
from app.services.git_service import GitService, RepositoryStateError
from app.services.handoff_service import HandoffService
from app.services.manifest_service import ManifestError, get_resource, remove_resource, replace_resource
from app.services.operations_service import OperationsService

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(require_github_client)])

_CLOUD_ORDER = {"oci": 0, "azure": 1, "gcp": 2}


def _cloud_sort_key(cloud: str) -> tuple[int, str]:
    return (_CLOUD_ORDER.get(cloud, 99), cloud)


def _region_options_with_selected(options: list[str], selected_region: str) -> list[str]:
    """Keep handoff-selected regions available even when config options lag behind."""
    if not selected_region or selected_region in options:
        return options
    return [selected_region, *options]


def _environment_options(project: str) -> list[str]:
    """Return the V2 environments permitted by the selected project layout."""
    installation = load_mccp_installation(settings.mccp_installation_path)
    if project.startswith("prod-"):
        return [installation.project_context(project, "prod").environment]
    return sorted(installation.nonprod_environments)

RequiredText = Annotated[str, StringConstraints(min_length=1)]
OptionalText = str


class DeployResourceForm(BaseModel):
    """Validated base fields for deploy-resource submissions."""
    model_config = ConfigDict(str_strip_whitespace=True)

    project: RequiredText
    template_path: RequiredText
    environment: RequiredText
    region: RequiredText
    change_reference: OptionalText = ""


class ResourceMutationForm(BaseModel):
    """Validated coordinates for an update or deletion request."""
    model_config = ConfigDict(str_strip_whitespace=True)

    project: RequiredText
    cloud: RequiredText
    environment: RequiredText
    region: RequiredText
    resource_path: RequiredText
    collection_name: RequiredText
    resource_key: RequiredText
    change_reference: OptionalText = ""


class UpdateResourceForm(ResourceMutationForm):
    """Validated resource replacement submitted from the generic editor."""
    resource_json: RequiredText


_REQUIRED_LABELS = {
    "project": "Project",
    "template_path": "Template path",
    "environment": "Environment",
    "region": "Region",
    "resource_path": "Manifest path",
    "collection_name": "Resource collection",
    "resource_key": "Resource key",
    "resource_json": "Resource JSON",
}
_SKIP_COLLECTION_NORMALIZATION = {
    "gcp_autonomous_databases_configuration",
}
_CUSTOM_ERRORS = {}
_EDITABLE_FIELD_PREFIX = "field:"
_SENSITIVE_EDITABLE_KEY_PARTS = ("password", "secret", "private_key", "token")
_NETWORK_PLACEHOLDER_LABELS = {
    "__PROJECT_NSG_CATEGORY__": "Project NSG Category",
    "__PROJECT_VCN_KEY__": "Project VCN Key",
    "__PROJECT_VCN_OCID__": "Project VCN OCID",
    "__PROJECT_NAME__": "Project Name",
    "__PROJ_APP_CMP_OCID__": "App Compartment OCID",
    "__PROJ_DB_CMP_OCID__": "DB Compartment OCID",
    "__NSG_WEB_KEY__": "Web NSG Key",
    "__NSG_WEB_DISPLAY_NAME__": "Web NSG Display Name",
    "__NSG_APP_KEY__": "App NSG Key",
    "__NSG_APP_DISPLAY_NAME__": "App NSG Display Name",
    "__NSG_DB_KEY__": "DB NSG Key",
    "__NSG_DB_DISPLAY_NAME__": "DB NSG Display Name",
    "__WEB_SOURCE_CIDR__": "Approved Client CIDR",
}
_OCI_ADB_ADMIN_PASSWORD_PLACEHOLDER = "__ADB_ADMIN_PASSWORD__"
_RUNTIME_SECRET_PLACEHOLDERS = {
    "__ADB_ADMIN_PASSWORD__",
    "__AZURE_ADB_ADMIN_PASSWORD__",
    "__AZURE_VM_SSH_PUBLIC_KEY__",
    "__GCP_VM_SSH_PUBLIC_KEY__",
}
_OCI_ADB_CONFIGURATION_KEY = "autonomous_databases_configuration"
_OCI_ADB_COLLECTION_KEY = "autonomous_databases"
_ACTIONS_SECRET_NAME_RE = re.compile(r"^[A-Z_][A-Z0-9_]*$")
_RUNTIME_SECRET_TOKEN_RE = re.compile(r"^__(DEV|TEST|UAT|PROD)_[A-Z_][A-Z0-9_]*__$")
_ACTIONS_SECRET_NAME_EXAMPLE = "ADB_PROD_PROJ9_02_ADMIN_PASSWORD"
_ACTIONS_SECRET_HELP = (
    "The secret must already exist in the selected project repository."
)


def _is_oci_adb_configuration(data: Any) -> bool:
    return isinstance(data, dict) and isinstance(
        data.get(_OCI_ADB_CONFIGURATION_KEY), dict
    )


def _is_oci_adb_admin_password_field(template: Any, field: dict) -> bool:
    return (
        _is_oci_adb_configuration(template)
        and field.get("placeholder") == _OCI_ADB_ADMIN_PASSWORD_PLACEHOLDER
        and str(field.get("path") or "").endswith(".admin_password")
    )


def _apply_oci_adb_secret_field_metadata(
    template: Any,
    fields: list[dict],
) -> None:
    for field in fields:
        if not _is_oci_adb_admin_password_field(template, field):
            continue
        field["label"] = "GitHub Actions secret name"
        field["input_type"] = "text"
        field["input_placeholder"] = _ACTIONS_SECRET_NAME_EXAMPLE
        field["help_text"] = _ACTIONS_SECRET_HELP

    for field in fields:
        if field.get("placeholder") not in _RUNTIME_SECRET_PLACEHOLDERS:
            continue
        field["label"] = "Environment secret name"
        field["input_type"] = "text"
        field["input_placeholder"] = "WORKLOAD_SECRET_NAME"
        field["help_text"] = (
            "Enter the repository-secret key without its environment prefix. "
            "The UI writes an environment-qualified runtime placeholder."
        )


def _prepare_runtime_secrets(
    template: Any,
    payload: dict[str, Any],
    environment: str,
) -> tuple[dict[str, Any], set[str], str | None]:
    prepared = dict(payload)
    allowed: set[str] = set()
    for placeholder in find_raw_placeholders(template) & _RUNTIME_SECRET_PLACEHOLDERS:
        secret_name = str(prepared.get(placeholder) or "").strip()
        wrapped = secret_name.startswith("__") and secret_name.endswith("__")
        if not _ACTIONS_SECRET_NAME_RE.fullmatch(secret_name) or wrapped:
            return prepared, set(), "Enter a valid environment secret name."
        token = f"__{environment.upper()}_{secret_name}__"
        prepared[placeholder] = token
        allowed.add(token)
    return prepared, allowed, None


def _validate_runtime_secret_values(value: Any, path: tuple[str, ...] = ()) -> None:
    """Reject literal secrets in the generic update editor."""
    if isinstance(value, dict):
        for key, child in value.items():
            _validate_runtime_secret_values(child, (*path, str(key)))
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            _validate_runtime_secret_values(child, (*path, str(index)))
        return
    if not isinstance(value, str) or not path:
        return

    field = path[-1].lower()
    if field.endswith(("password", "private_key", "ssh_public_key")):
        if not _RUNTIME_SECRET_TOKEN_RE.fullmatch(value):
            raise ValueError(
                "Resource JSON must use an environment-qualified runtime placeholder "
                "for password and key fields."
            )


def _is_oci_adb_admin_password_path(path: tuple[str, ...]) -> bool:
    return (
        len(path) >= 4
        and path[0] == _OCI_ADB_CONFIGURATION_KEY
        and _OCI_ADB_COLLECTION_KEY in path
        and path[-1] == "admin_password"
    )


def _find_disallowed_placeholders(
    value: Any,
    allowed_runtime_secret_tokens: set[str],
    path: tuple[str, ...] = (),
) -> set[str]:
    unresolved: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(key, str):
                unresolved.update(find_raw_placeholders(key))
            unresolved.update(
                _find_disallowed_placeholders(
                    item,
                    allowed_runtime_secret_tokens,
                    (*path, str(key)),
                )
            )
        return unresolved
    if isinstance(value, list):
        for index, item in enumerate(value):
            unresolved.update(
                _find_disallowed_placeholders(
                    item,
                    allowed_runtime_secret_tokens,
                    (*path, str(index)),
                )
            )
        return unresolved
    if not isinstance(value, str):
        return unresolved

    tokens = find_raw_placeholders(value)
    if value in allowed_runtime_secret_tokens:
        tokens.discard(value)
    unresolved.update(tokens)
    return unresolved


def _collection_paths(data: dict, path: tuple[str, ...] = ()) -> list[tuple[str, tuple[str, ...], dict]]:
    """Find Terraform resource collection maps, e.g. autonomous_databases."""
    matches = []
    for key, value in (data or {}).items():
        if not isinstance(value, dict):
            continue
        current_path = (*path, key)
        if key in DashboardService.RESOURCE_KEYS:
            matches.append((key, current_path, value))
        matches.extend(_collection_paths(value, current_path))
    return matches


def _empty_value_for_type(value: Any, key: str) -> Any:
    """Return a Terraform type-compatible empty value for inferred map attributes."""
    if isinstance(value, bool):
        return False
    if isinstance(value, str):
        if key in {"db_version"} or key.endswith("_version"):
            return value
        return ""
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return value
    if isinstance(value, list):
        return []
    if isinstance(value, dict):
        return {}
    return None


def _normalize_object_shapes(objects: list[dict]) -> None:
    """Make sibling Terraform objects share attribute names and non-null value types."""
    keys = set()
    for obj in objects:
        keys.update(obj)

    for key in sorted(keys):
        default_value = None
        for obj in objects:
            if key not in obj or obj[key] is None:
                continue
            default_value = _empty_value_for_type(obj[key], key)
            break

        for obj in objects:
            if key not in obj or (obj[key] is None and default_value is not None):
                obj[key] = deepcopy(default_value)

        nested = [
            obj[key]
            for obj in objects
            if isinstance(obj.get(key), dict)
        ]
        if nested:
            _normalize_object_shapes(nested)


def _normalize_collection_shape(resource_key: str, collection: dict) -> None:
    """Keep Terraform for_each maps homogeneous after additive merges."""
    if resource_key in _SKIP_COLLECTION_NORMALIZATION:
        return
    resource_objects = [
        value
        for value in collection.values()
        if isinstance(value, dict)
    ]
    if not resource_objects:
        return
    _normalize_object_shapes(resource_objects)


def _normalize_resource_collections(data: dict) -> dict:
    """Return data with all known resource collection maps normalized."""
    normalized = deepcopy(data)
    for resource_key, _, collection in _collection_paths(normalized):
        _normalize_collection_shape(resource_key, collection)
    return normalized


def _is_network_configuration(data: dict) -> bool:
    """Return whether the rendered template is an OCI network configuration manifest."""
    return isinstance((data or {}).get("network_configuration"), dict)


def _is_gcp_adb_configuration(cloud: str, data: dict) -> bool:
    """Return whether the rendered template belongs in the canonical GCP ADB manifest."""
    return (
        cloud == "gcp"
        and isinstance((data or {}).get("gcp_autonomous_databases_configuration"), dict)
    )


def _canonical_resource_target(cloud: str, data: dict) -> tuple[str, str, bool]:
    """Return the canonical manifest stem, path, and same-root search behavior."""
    cloud_key = (cloud or "").lower()
    collection_names = {name for name, _, _ in _collection_paths(data)}

    if cloud_key == "oci" and _is_network_configuration(data):
        return "project-nsgs", "network/project-nsgs.json", False
    if _is_gcp_adb_configuration(cloud_key, data):
        return "adb", "workloads/adb.json", False

    if cloud_key == "oci":
        if {"autonomous_databases", "databases"} & collection_names:
            return "database", "database/database.json", True
        if {"compute_instances", "instances"} & collection_names:
            return "compute", "compute/compute.json", True

    if cloud_key == "azure":
        if {"virtual_machines", "compute_instances", "instances"} & collection_names:
            return "compute", "compute/compute.json", True
        if {"oracle_autonomous_databases", "autonomous_databases", "databases"} & collection_names:
            return "database", "database/database.json", True

    if cloud_key == "gcp":
        if "gcp_virtual_machines_configuration" in collection_names:
            return "compute", "compute/compute.json", False

    if collection_names:
        stem = sorted(collection_names)[0].replace("_", "-")
        return stem, f"workloads/{stem}.json", True
    return "resource", "workloads/resource.json", True


def _strip_optional_placeholders(data: Any, optional_placeholders: set[str]) -> Any:
    """Remove unresolved optional placeholders from rendered list values."""
    if isinstance(data, list):
        cleaned = []
        for item in data:
            if isinstance(item, str) and item in optional_placeholders:
                continue
            cleaned.append(_strip_optional_placeholders(item, optional_placeholders))
        return cleaned
    if isinstance(data, dict):
        return {
            key: _strip_optional_placeholders(value, optional_placeholders)
            for key, value in data.items()
        }
    return data


def _is_nsg_selector_field(field: dict[str, Any]) -> bool:
    placeholder = (field.get("placeholder") or "").lower()
    label = (field.get("label") or "").lower()
    path = (field.get("path") or "").lower()
    return "nsg" in placeholder or "nsg" in label or "network_security_groups" in path


def _is_compartment_selector_field(field: dict[str, Any]) -> bool:
    """Identify fields that accept an OCI compartment OCID."""
    placeholder = (field.get("placeholder") or "").lower()
    path = (field.get("path") or "").lower()
    return (
        "compartment" in placeholder
        or path.endswith(".default_compartment_id")
        or path.endswith(".compartment_id")
        or path.endswith(".compartment_ocid")
    )


def _normalize_nsg_tier(value: str) -> str:
    lowered = (value or "").lower()
    if "database" in lowered or re.search(r"(^|[^a-z0-9])db([^a-z0-9]|$)", lowered):
        return "db"
    if re.search(r"(^|[^a-z0-9])app([^a-z0-9]|$)", lowered):
        return "app"
    if re.search(r"(^|[^a-z0-9])web([^a-z0-9]|$)", lowered):
        return "web"
    if re.search(r"(^|[^a-z0-9])infra([^a-z0-9]|$)", lowered):
        return "infra"
    return ""


def _nsg_tier_for_option(key: str, nsg: Any) -> str:
    values = [key]
    if isinstance(nsg, dict):
        values.append(str(nsg.get("display_name") or ""))
        tags = nsg.get("freeform_tags")
        if isinstance(tags, dict):
            values.extend(str(value) for value in tags.values())
    for value in values:
        tier = _normalize_nsg_tier(value)
        if tier:
            return tier
    return ""


def _nsg_tier_for_field(field: dict[str, Any]) -> str:
    for value in (field.get("placeholder"), field.get("label"), field.get("path")):
        tier = _normalize_nsg_tier(str(value or ""))
        if tier:
            return tier
    return ""


def _nsg_options_for_field(
    field: dict[str, Any],
    options: list[dict[str, str]],
) -> list[dict[str, str]]:
    tier = _nsg_tier_for_field(field)
    if not tier:
        return options
    return [option for option in options if option.get("tier") == tier]


def _extract_nsg_options(node: Any) -> list[dict[str, str]]:
    """Extract project NSG keys/display names from the aggregated network manifest."""
    options: dict[str, dict[str, str]] = {}

    def _walk(value: Any) -> None:
        if isinstance(value, dict):
            nsgs = value.get("network_security_groups")
            if isinstance(nsgs, dict):
                for key, nsg in nsgs.items():
                    if not isinstance(key, str) or not key:
                        continue
                    display_name = ""
                    if isinstance(nsg, dict):
                        display_name = str(nsg.get("display_name") or "")
                    options[key] = {
                        "value": key,
                        "label": f"{display_name} ({key})" if display_name else key,
                        "tier": _nsg_tier_for_option(key, nsg),
                    }
            for child in value.values():
                _walk(child)
        elif isinstance(value, list):
            for child in value:
                _walk(child)

    _walk(node)
    return [
        option
        for _, option in sorted(options.items(), key=lambda item: item[0].lower())
    ]


async def _load_project_nsg_options(
    git: GitService,
    cloud: str,
    environment: str,
    region: str,
) -> list[dict[str, str]]:
    """Return OCI project NSG selectors for a region when the project manifest exists."""
    if (cloud or "").lower() != "oci" or not region:
        return []
    try:
        manifest = await git.read_manifest(
            cloud,
            environment,
            region,
            "network/project-nsgs.json",
        )
    except Exception:
        return []
    return _extract_nsg_options(manifest)


def _path_tokens(path: str) -> list[str]:
    tokens: list[str] = []
    for part in (path or "").replace("[", ".[").split("."):
        if not part:
            continue
        tokens.append(part.split("[", 1)[0] if "[" in part else part)
    return [token for token in tokens if token]


def _is_sensitive_editable_path(path: str) -> bool:
    lowered = (path or "").lower()
    return any(part in lowered for part in _SENSITIVE_EDITABLE_KEY_PARTS)


def _is_editable_default_value(path: str, value: Any) -> bool:
    if _is_sensitive_editable_path(path):
        return False
    if isinstance(value, str):
        return not find_raw_placeholders(value)
    return isinstance(value, (bool, int, float))


def _is_resource_context_path(path: str) -> bool:
    tokens = set(_path_tokens(path))
    return bool(tokens & set(DashboardService.RESOURCE_KEYS))


def _editable_value_type(value: Any) -> str:
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    return "str"


def _editable_input_type(value_type: str) -> str:
    return "number" if value_type in {"int", "float"} else "text"


def _editable_label(path: str) -> str:
    leaf = _path_tokens(path)[-1] if _path_tokens(path) else path
    return leaf.replace("_", " ").title()


def _extract_editable_default_fields(obj: dict | list) -> list[dict[str, Any]]:
    """Expose scalar template defaults under resource maps as editable form fields."""
    fields: list[dict[str, Any]] = []

    def _walk(node: Any, path: str = "") -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                child_path = f"{path}.{key}" if path else str(key)
                if isinstance(value, (dict, list)):
                    _walk(value, child_path)
                elif _is_resource_context_path(child_path) and _is_editable_default_value(child_path, value):
                    value_type = _editable_value_type(value)
                    fields.append(
                        {
                            "path": child_path,
                            "name": f"{_EDITABLE_FIELD_PREFIX}{child_path}",
                            "label": _editable_label(child_path),
                            "key": child_path,
                            "required": True,
                            "suggested_value": value,
                            "value_type": value_type,
                            "input_type": _editable_input_type(value_type),
                        }
                    )
        elif isinstance(node, list):
            for idx, value in enumerate(node):
                _walk(value, f"{path}[{idx}]")

    _walk(obj)
    return fields


def _editable_default_fields_for_template(obj: dict | list) -> list[dict[str, Any]]:
    """Return editable scalar defaults for workload templates only."""
    if isinstance(obj, dict) and _is_network_configuration(obj):
        return []
    return _extract_editable_default_fields(obj)


def _apply_template_specific_field_labels(obj: dict | list, fields: list[dict[str, Any]]) -> None:
    """Make network form placeholders read as product concepts instead of JSON keys."""
    if not isinstance(obj, dict) or not _is_network_configuration(obj):
        return
    for field in fields:
        placeholder = field.get("placeholder")
        if placeholder in _NETWORK_PLACEHOLDER_LABELS:
            field["label"] = _NETWORK_PLACEHOLDER_LABELS[placeholder]


def _parse_editable_path(path: str) -> list[str | int]:
    segments: list[str | int] = []
    for part in (path or "").split("."):
        remaining = part
        while remaining:
            if "[" not in remaining:
                segments.append(remaining)
                break
            before, after = remaining.split("[", 1)
            if before:
                segments.append(before)
            index, _, remaining = after.partition("]")
            segments.append(int(index))
    return segments


def _coerce_editable_value(raw_value: Any, value_type: str, field_name: str) -> Any:
    raw_text = str(raw_value)
    if value_type == "bool":
        lowered = raw_text.strip().lower()
        if lowered in {"true", "1", "yes", "on"}:
            return True
        if lowered in {"false", "0", "no", "off"}:
            return False
        raise ValueError(f"Invalid boolean value for {field_name}")
    if value_type == "int":
        try:
            return int(raw_text)
        except ValueError as exc:
            raise ValueError(f"Invalid integer value for {field_name}") from exc
    if value_type == "float":
        try:
            return float(raw_text)
        except ValueError as exc:
            raise ValueError(f"Invalid number value for {field_name}") from exc
    return raw_text


def _set_nested_value(data: dict | list, segments: list[str | int], value: Any) -> None:
    target: Any = data
    for segment in segments[:-1]:
        target = target[segment]
    target[segments[-1]] = value


def _apply_editable_default_overrides(
    data: dict,
    payload: dict[str, Any],
    editable_fields: list[dict[str, Any]],
    placeholders: set[str],
) -> dict:
    updated = deepcopy(data)
    for field in editable_fields:
        field_name = field["name"]
        if field_name not in payload:
            continue
        path_placeholders = find_raw_placeholders(field["path"]) & placeholders
        rendered_path, missing = fill_template_with_missing(
            field["path"],
            payload,
            path_placeholders,
        )
        if missing:
            continue
        value = _coerce_editable_value(
            payload[field_name],
            field["value_type"],
            field["label"],
        )
        _set_nested_value(updated, _parse_editable_path(str(rendered_path)), value)
    return updated


def _can_use_catalog_pat(client) -> bool:
    """Return whether the server PAT can be used for gitops-templates catalog reads."""
    return (
        bool(settings.github_token)
        and isinstance(client, GitHubClient)
        and client is not default_github_client
    )


async def _resource_catalog_with_entries(github_client) -> tuple[CatalogService, list]:
    """Return catalog entries, falling back to the server PAT only for gitops-templates."""
    catalog = GitService._catalog_service(github_client)
    try:
        entries = await catalog.list_resources_catalog_entries()
    except Exception:
        if not _can_use_catalog_pat(github_client):
            raise
        fallback_catalog = GitService._catalog_service(default_github_client)
        return fallback_catalog, await fallback_catalog.list_resources_catalog_entries()

    if not entries and _can_use_catalog_pat(github_client):
        fallback_catalog = GitService._catalog_service(default_github_client)
        fallback_entries = await fallback_catalog.list_resources_catalog_entries()
        if fallback_entries:
            return fallback_catalog, fallback_entries
    return catalog, entries


async def _load_catalog_resource_template(github_client, template_path: str):
    """Load a resource template only when it is advertised by the resources catalog."""
    catalog, entries = await _resource_catalog_with_entries(github_client)
    allowed_paths = {
        entry.id
        for entry in entries
    }
    if template_path not in allowed_paths:
        raise ValueError(f"Template is not available in the resources catalog: {template_path}")
    template = await catalog.load_json_template(template_path)
    if not template:
        raise ValueError(f"Template not found: {template_path}")
    return template


def _network_vcn_identifiers(category: dict) -> set[str]:
    vcn_map = (category or {}).get("inject_into_existing_vcns", {})
    if not isinstance(vcn_map, dict):
        return set()
    identifiers = set(vcn_map)
    identifiers.update(
        value.get("vcn_id")
        for value in vcn_map.values()
        if isinstance(value, dict) and isinstance(value.get("vcn_id"), str)
    )
    return identifiers


def _align_network_categories(existing: dict, incoming: dict) -> dict:
    """Reuse the declared category when an NSG targets an existing VCN."""
    existing_categories = (
        existing.get("network_configuration", {})
        .get("network_configuration_categories", {})
    )
    incoming_copy = deepcopy(incoming)
    incoming_categories = (
        incoming_copy.get("network_configuration", {})
        .get("network_configuration_categories", {})
    )
    if not isinstance(existing_categories, dict) or not isinstance(incoming_categories, dict):
        return incoming_copy

    for incoming_key in list(incoming_categories):
        incoming_category = incoming_categories[incoming_key]
        incoming_identifiers = _network_vcn_identifiers(incoming_category)
        if not incoming_identifiers:
            continue
        matching_categories = [
            existing_key
            for existing_key, existing_category in existing_categories.items()
            if incoming_identifiers & _network_vcn_identifiers(existing_category)
        ]
        if len(matching_categories) > 1:
            raise ValueError("Cannot safely merge NSG because its VCN appears in multiple categories")
        if not matching_categories or matching_categories[0] == incoming_key:
            continue
        existing_key = matching_categories[0]
        if existing_key in incoming_categories:
            raise ValueError("Cannot safely merge multiple NSG categories for the same VCN")
        incoming_categories[existing_key] = incoming_categories.pop(incoming_key)
    return incoming_copy


def _merge_resource_dict(existing: dict, incoming: dict, path: tuple[str, ...] = ()) -> dict:
    """Merge incoming resource entries without replacing existing Terraform maps."""
    if not path:
        incoming = _align_network_categories(existing, incoming)
    merged = deepcopy(existing)
    for key, incoming_value in incoming.items():
        current_path = (*path, key)
        if key not in merged:
            if key in DashboardService.RESOURCE_KEYS and isinstance(incoming_value, dict):
                matching_paths = [
                    collection_path
                    for name, collection_path, _ in _collection_paths(merged)
                    if name == key
                ]
                if len(matching_paths) == 1:
                    target = merged
                    for path_part in matching_paths[0]:
                        target = target[path_part]
                    duplicates = sorted(set(target) & set(incoming_value))
                    if duplicates:
                        raise ValueError(
                            f"Resource key already exists in manifest: {', '.join(duplicates)}"
                        )
                    target.update(deepcopy(incoming_value))
                    _normalize_collection_shape(key, target)
                    continue
                if len(matching_paths) > 1:
                    raise ValueError(
                        f"Cannot safely merge resource manifest because multiple '{key}' maps exist"
                    )
            merged[key] = deepcopy(incoming_value)
            continue

        existing_value = merged[key]
        if (
            key in DashboardService.RESOURCE_KEYS
            and isinstance(existing_value, dict)
            and isinstance(incoming_value, dict)
        ):
            duplicates = sorted(set(existing_value) & set(incoming_value))
            if duplicates:
                raise ValueError(
                    f"Resource key already exists in manifest: {', '.join(duplicates)}"
                )
            existing_value.update(deepcopy(incoming_value))
            _normalize_collection_shape(key, existing_value)
            continue

        if isinstance(existing_value, dict) and isinstance(incoming_value, dict):
            merged[key] = _merge_resource_dict(existing_value, incoming_value, current_path)
            continue

        if existing_value != incoming_value:
            dotted = ".".join(current_path)
            raise ValueError(
                f"Cannot safely merge resource manifest because '{dotted}' differs from the existing file"
            )

    for resource_key, _, collection in _collection_paths(merged):
        _normalize_collection_shape(resource_key, collection)
    return merged


async def _resolve_resource_write(
    git: GitService,
    cloud: str,
    environment: str,
    region: str,
    target_resource_path: str,
    data: dict,
    *,
    search_existing_collections: bool = True,
) -> tuple[str, dict]:
    """Return the safest workload path/data for additive Terraform map updates."""
    structure = await git.get_repository_structure(strict=True)
    incoming_collections = {name for name, _, _ in _collection_paths(data)}
    if not incoming_collections:
        return target_resource_path, data

    target_full_path = f"{cloud}/{environment}/{region}/{target_resource_path}"
    target_exists = False
    existing_manifests: list[tuple[str, str, dict]] = []

    for cloud_entry in structure.get("clouds", []):
        if cloud_entry.get("name") != cloud:
            continue
        for region_entry in cloud_entry.get("regions", []):
            if (
                region_entry.get("environment") != environment
                or region_entry.get("name") != region
            ):
                continue
            for resource in sorted(region_entry.get("resources", []), key=lambda item: item.get("path", "")):
                full_path = resource.get("path", "")
                if full_path == target_full_path:
                    target_exists = True
                prefix = f"{cloud}/{environment}/{region}/"
                if not full_path.startswith(prefix) or not full_path.endswith(".json"):
                    continue
                relative_path = full_path[len(prefix):]
                if relative_path.startswith("lifecycle_operations/"):
                    continue
                if not search_existing_collections and full_path != target_full_path:
                    continue

                existing = await git.read_manifest(
                    cloud,
                    environment,
                    region,
                    relative_path,
                    strict=True,
                )
                if not isinstance(existing, dict):
                    raise RepositoryStateError(
                        f"Manifest is not a JSON object: {full_path}"
                    )
                existing_manifests.append((full_path, relative_path, existing))

    for full_path, relative_path, existing in existing_manifests:
        if full_path == target_full_path:
            return relative_path, _merge_resource_dict(existing, data)

        existing_collections = {name for name, _, _ in _collection_paths(existing)}
        if incoming_collections.isdisjoint(existing_collections):
            continue
        return relative_path, _merge_resource_dict(existing, data)

    if target_exists:
        raise ValueError(f"Manifest already exists and cannot be safely merged: {target_full_path}")
    return target_resource_path, _normalize_resource_collections(data)


@router.get("/resources", response_class=HTMLResponse)
async def resources_partial(
    request: Request,
    project: ProjectSelected,
) -> HTMLResponse:
    """List deployed resources in project."""
    load_error = ""
    try:
        github_client = request.state.github_client
        git = GitService(project, github_client=github_client)
        dashboard = DashboardService(git)
        inventory = await dashboard.get_resource_inventory(strict=True)
        resources = inventory.get("resources", [])

        # Fetch operations catalog once and annotate each resource.
        catalog = await git.get_operations_catalog()
        all_ops = [operation for operation in catalog.operations if operation.cloud == "oci"]
        resources = OperationsService.attach_matches(resources, all_ops)
        for resource in resources:
            if resource.get("environment") not in {"dev", "test", "uat"}:
                resource["ops"] = []
    except RepositoryStateError as exc:
        logger.error("Unable to verify resources for %s: %s", project, exc, exc_info=True)
        return render_repository_state_error(request)
    except Exception as exc:
        logger.error("Error loading resources for %s: %s", project, exc, exc_info=True)
        resources = []
        load_error = "resources"

    return render_partial(
        "partials/resources.html",
        request,
        project=project,
        resources=resources,
        load_error=load_error,
    )


@router.get("/manifest", response_class=HTMLResponse)
async def manifest_partial(
    request: Request,
    path: str,
    project: ProjectSelected,
) -> HTMLResponse:
    """View manifest file content."""
    try:
        github_client = request.state.github_client
        git = GitService(project, github_client=github_client)
        parts = path.split("/")
        cloud, environment, region = parts[0], parts[1], parts[2]
        resource_path = "/".join(parts[3:])
        content = await git.read_manifest(cloud, environment, region, resource_path)
    except Exception as exc:
        content = {"error": str(exc)}

    return render_partial("partials/manifest.html", request, project=project, path=path, content=content)


@router.get("/resources-catalog", response_class=HTMLResponse)
async def resources_catalog_partial(
    request: Request,
    project: ProjectRead,
    environment: str = Query("dev"),
) -> HTMLResponse:
    """List available resources to deploy from resources-catalog."""
    try:
        github_client = request.state.github_client
        _, entries = await _resource_catalog_with_entries(github_client)
        resources_by_cloud = {}
        for entry in entries:
            resources_by_cloud.setdefault(entry.cloud, []).append(entry.model_dump())
        resources_by_cloud = {
            cloud: sorted(resources, key=lambda item: (item["category"], item["name"]))
            for cloud, resources in sorted(
                resources_by_cloud.items(),
                key=lambda item: _cloud_sort_key(item[0]),
            )
        }
    except Exception as exc:
        logger.error("Error loading resources catalog: %s", exc, exc_info=True)
        return render_partial(
            "partials/state-error.html",
            request,
            title="Error loading resources catalog",
            message=str(exc),
        )

    return render_partial(
        "partials/resources-catalog.html",
        request,
        project=project,
        environment=environment if environment in _environment_options(project) else _environment_options(project)[0],
        environment_options=_environment_options(project),
        resources_by_cloud=resources_by_cloud,
    )


@router.get("/resource-form", response_class=HTMLResponse)
async def resource_form_partial(
    request: Request,
    project: ProjectRead,
    path: str = Query(...),
    environment: str = Query("dev"),
) -> HTMLResponse:
    """Show dynamic form to deploy a resource."""
    try:
        environment_options = _environment_options(project)
        if environment not in environment_options:
            raise ValueError("Selected environment is not allowed for this project repository")
        github_client = request.state.github_client
        template = await _load_catalog_resource_template(github_client, path)
        fields = extract_form_fields(template.content)
        _apply_template_specific_field_labels(template.content, fields)
        _apply_oci_adb_secret_field_metadata(template.content, fields)
        for field in fields:
            field["name"] = field["placeholder"]
        fields.extend(_editable_default_fields_for_template(template.content))
        handoff = HandoffService(github_client, project, environment)
        handoff_suggestions = await handoff.load_suggestions(
            template_path=path,
        )
        compartment_options = await handoff.load_compartment_options()
        for field in fields:
            placeholder = field.get("placeholder")
            if placeholder:
                field["suggested_value"] = handoff_suggestions.get(placeholder, "")
            if compartment_options and _is_compartment_selector_field(field):
                field["options"] = compartment_options
        cloud = template.cloud or settings.default_cloud
        default_region = settings.default_region_for_cloud(cloud)
        selected_region = handoff_suggestions.get("__REGION__") or default_region
        region_options = settings.region_options_for_cloud(cloud)
        region_options = _region_options_with_selected(region_options, selected_region)
        git = GitService(project, github_client=github_client)
        nsg_options = (
            []
            if _is_network_configuration(template.content)
            else await _load_project_nsg_options(
                git,
                cloud,
                environment,
                selected_region,
            )
        )
        if nsg_options:
            for field in fields:
                if _is_nsg_selector_field(field):
                    options = _nsg_options_for_field(field, nsg_options)
                    if options:
                        field["options"] = options
    except Exception as exc:
        logger.error("Error loading resource form: %s", exc, exc_info=True)
        return render_partial(
            "partials/state-error.html",
            request,
            title="Error loading resource form",
            message=str(exc),
        )

    return render_partial(
        "partials/resource-form.html",
        request,
        project=project,
        template_path=path,
        environment=environment,
        environment_options=environment_options,
        cloud=cloud,
        default_region=default_region,
        selected_region=selected_region,
        region_options=region_options,
        fields=fields,
    )


@router.post("/deploy-resource", response_class=HTMLResponse)
async def deploy_resource_submit(
    request: Request,
) -> HTMLResponse:
    """Deploy the resource to the project repo."""
    payload = await request_form_payload(request)

    try:
        form = DeployResourceForm.model_validate(payload)
    except ValidationError as exc:
        error = "; ".join(
            validation_messages(
                exc,
                required_labels=_REQUIRED_LABELS,
                custom_errors=_CUSTOM_ERRORS,
            )
        )
        return render_partial("partials/deploy-result.html", request, **htmx_error_context(escape(error)))

    project = form.project
    await ensure_project_write_access(request, project)

    try:
        if form.environment not in _environment_options(project):
            raise ValueError("Selected environment is not allowed for this project repository")
        github_client = request.state.github_client
        template = await _load_catalog_resource_template(github_client, form.template_path)

        payload, allowed_runtime_secret_tokens, secret_error = _prepare_runtime_secrets(
            template.content,
            payload,
            form.environment,
        )
        if secret_error:
            return render_partial(
                "partials/deploy-result.html",
                request,
                **htmx_error_context(secret_error),
            )

        fields = extract_form_fields(template.content)
        editable_fields = _editable_default_fields_for_template(template.content)
        optional_placeholders = {
            field["placeholder"]
            for field in fields
            if not field.get("required", True)
        }
        placeholders = find_raw_placeholders(template.content)
        data, missing_placeholders = fill_template_with_missing(
            template.content,
            payload,
            placeholders,
        )
        missing_required = [
            placeholder
            for placeholder in missing_placeholders
            if placeholder not in optional_placeholders
        ]
        if missing_required:
            logger.warning(
                "Template %s missing placeholder values: %s",
                form.template_path,
                missing_required,
            )
            missing = ", ".join(sorted(missing_required))
            return render_partial(
                "partials/deploy-result.html",
                request,
                **htmx_error_context(escape(f"Missing values: {missing}")),
            )
        if optional_placeholders:
            data = _strip_optional_placeholders(data, optional_placeholders)

        if not isinstance(data, dict):
            raise ValueError(f"Template did not render to a JSON object: {form.template_path}")
        unresolved_placeholders = sorted(
            _find_disallowed_placeholders(data, allowed_runtime_secret_tokens)
        )
        if unresolved_placeholders:
            unresolved = ", ".join(unresolved_placeholders)
            return render_partial(
                "partials/deploy-result.html",
                request,
                **htmx_error_context(escape(f"Unresolved placeholders: {unresolved}")),
            )
        if editable_fields:
            data = _apply_editable_default_overrides(
                data,
                payload,
                editable_fields,
                placeholders,
            )

        cloud = template.cloud or settings.default_cloud
        resource_id, target_resource_path, search_existing_collections = _canonical_resource_target(
            cloud,
            data,
        )
        filename = f"{resource_id}.json"
        environment = form.environment
        region = form.region

        change_reference = form.change_reference.strip()
        base_msg = f"Day-1: Deploy {filename}"
        commit_message = f"[{change_reference}] {base_msg}" if change_reference else base_msg

        git = GitService(project, github_client=github_client)
        resource_path, data = await _resolve_resource_write(
            git=git,
            cloud=cloud,
            environment=environment,
            region=region,
            target_resource_path=target_resource_path,
            data=data,
            search_existing_collections=search_existing_collections,
        )
        result = await git.write_manifest(
            cloud=cloud,
            environment=environment,
            region=region,
            resource_path=resource_path,
            data=data,
            commit_message=commit_message,
        )

        return render_partial(
            "partials/deploy-result.html",
            request,
            success=True,
            pr_number=result.get("pr_number", "N/A"),
            pr_url=result.get("pr_url", "#"),
            filename=filename,
            project=project,
        )

    except RepositoryStateError as exc:
        logger.error("Repository verification failed during deploy: %s", exc, exc_info=True)
        return render_repository_state_error(request)
    except Exception as exc:
        logger.error("Error deploying resource: %s", exc, exc_info=True)
        return render_partial("partials/deploy-result.html", request, **htmx_error_context(escape(str(exc))))


async def _load_resource_for_mutation(
    *,
    project: str,
    github_client: Any,
    cloud: str,
    environment: str,
    region: str,
    resource_path: str,
    collection_name: str,
    resource_key: str,
) -> tuple[GitService, dict[str, Any], dict[str, Any]]:
    """Load one resource through its V2 manifest coordinates."""
    if environment not in _environment_options(project):
        raise ValueError("Selected environment is not allowed for this project repository")
    if cloud not in _CLOUD_ORDER:
        raise ValueError("Cloud is not supported by the MCCP catalog")
    if collection_name not in DashboardService.RESOURCE_KEYS:
        raise ValueError("Resource collection is not supported by the MCCP catalog")

    git = GitService(project, github_client=github_client)
    manifest = await git.read_manifest(
        cloud,
        environment,
        region,
        resource_path,
        strict=True,
    )
    if not isinstance(manifest, dict):
        raise ManifestError("Manifest is not a JSON object")
    resource = get_resource(
        manifest,
        collection_name=collection_name,
        resource_key=resource_key,
    )
    return git, manifest, resource


def _resource_mutation_result(
    request: Request,
    *,
    action: str,
    result: dict[str, Any],
    project: str,
    resource_key: str,
) -> HTMLResponse:
    """Render the shared PR result for all Day-1 resource mutations."""
    return render_partial(
        "partials/deploy-result.html",
        request,
        success=True,
        action=action,
        pr_number=result.get("pr_number", "N/A"),
        pr_url=result.get("pr_url", "#"),
        filename=resource_key,
        project=project,
    )


@router.get("/resource-edit", response_class=HTMLResponse)
async def resource_edit_form(
    request: Request,
    project: ProjectRead,
    cloud: str = Query(...),
    environment: str = Query(...),
    region: str = Query(...),
    resource_path: str = Query(...),
    collection_name: str = Query(...),
    resource_key: str = Query(...),
) -> HTMLResponse:
    """Show the generic JSON editor for one existing Day-1 resource."""
    try:
        _, _, resource = await _load_resource_for_mutation(
            project=project,
            github_client=request.state.github_client,
            cloud=cloud,
            environment=environment,
            region=region,
            resource_path=resource_path,
            collection_name=collection_name,
            resource_key=resource_key,
        )
    except RepositoryStateError as exc:
        logger.error("Unable to verify resource for update: %s", exc, exc_info=True)
        return render_repository_state_error(request)
    except Exception as exc:
        logger.error("Unable to load resource for update: %s", exc, exc_info=True)
        return render_partial(
            "partials/state-error.html",
            request,
            title="Error loading resource",
            message=str(exc),
        )

    return render_partial(
        "partials/resource-edit.html",
        request,
        project=project,
        cloud=cloud,
        environment=environment,
        region=region,
        resource_path=resource_path,
        collection_name=collection_name,
        resource_key=resource_key,
        resource_json=json.dumps(resource, indent=2),
    )


@router.post("/update-resource", response_class=HTMLResponse)
async def update_resource_submit(request: Request) -> HTMLResponse:
    """Replace one existing aggregate resource entry through a pull request."""
    payload = await request_form_payload(request)
    try:
        form = UpdateResourceForm.model_validate(payload)
    except ValidationError as exc:
        error = "; ".join(validation_messages(exc, required_labels=_REQUIRED_LABELS))
        return render_partial("partials/deploy-result.html", request, **htmx_error_context(escape(error)))

    await ensure_project_write_access(request, form.project)
    try:
        try:
            replacement = json.loads(form.resource_json)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Resource JSON is invalid: {exc.msg}") from exc
        if not isinstance(replacement, dict):
            raise ValueError("Resource JSON must be an object")
        _validate_runtime_secret_values(replacement)

        git, manifest, _ = await _load_resource_for_mutation(
            project=form.project,
            github_client=request.state.github_client,
            cloud=form.cloud,
            environment=form.environment,
            region=form.region,
            resource_path=form.resource_path,
            collection_name=form.collection_name,
            resource_key=form.resource_key,
        )
        data = replace_resource(
            manifest,
            collection_name=form.collection_name,
            resource_key=form.resource_key,
            replacement=replacement,
        )
        reference = form.change_reference.strip()
        message = f"Day-1: Update {form.resource_key}"
        if reference:
            message = f"[{reference}] {message}"
        result = await git.write_manifest(
            form.cloud,
            form.environment,
            form.region,
            form.resource_path,
            data,
            commit_message=message,
        )
        return _resource_mutation_result(
            request,
            action="updated",
            result=result,
            project=form.project,
            resource_key=form.resource_key,
        )
    except RepositoryStateError as exc:
        logger.error("Repository verification failed during update: %s", exc, exc_info=True)
        return render_repository_state_error(request)
    except Exception as exc:
        logger.error("Error updating resource: %s", exc, exc_info=True)
        return render_partial("partials/deploy-result.html", request, **htmx_error_context(escape(str(exc))))


@router.get("/resource-delete", response_class=HTMLResponse)
async def resource_delete_form(
    request: Request,
    project: ProjectRead,
    cloud: str = Query(...),
    environment: str = Query(...),
    region: str = Query(...),
    resource_path: str = Query(...),
    collection_name: str = Query(...),
    resource_key: str = Query(...),
) -> HTMLResponse:
    """Show a confirmation page for one resource deletion request."""
    try:
        await _load_resource_for_mutation(
            project=project,
            github_client=request.state.github_client,
            cloud=cloud,
            environment=environment,
            region=region,
            resource_path=resource_path,
            collection_name=collection_name,
            resource_key=resource_key,
        )
    except RepositoryStateError as exc:
        logger.error("Unable to verify resource for deletion: %s", exc, exc_info=True)
        return render_repository_state_error(request)
    except Exception as exc:
        logger.error("Unable to load resource for deletion: %s", exc, exc_info=True)
        return render_partial(
            "partials/state-error.html",
            request,
            title="Error loading resource",
            message=str(exc),
        )

    return render_partial(
        "partials/resource-delete.html",
        request,
        project=project,
        cloud=cloud,
        environment=environment,
        region=region,
        resource_path=resource_path,
        collection_name=collection_name,
        resource_key=resource_key,
    )


@router.post("/delete-resource", response_class=HTMLResponse)
async def delete_resource_submit(request: Request) -> HTMLResponse:
    """Remove one existing aggregate resource entry through a pull request."""
    payload = await request_form_payload(request)
    try:
        form = ResourceMutationForm.model_validate(payload)
    except ValidationError as exc:
        error = "; ".join(validation_messages(exc, required_labels=_REQUIRED_LABELS))
        return render_partial("partials/deploy-result.html", request, **htmx_error_context(escape(error)))

    await ensure_project_write_access(request, form.project)
    try:
        git, manifest, _ = await _load_resource_for_mutation(
            project=form.project,
            github_client=request.state.github_client,
            cloud=form.cloud,
            environment=form.environment,
            region=form.region,
            resource_path=form.resource_path,
            collection_name=form.collection_name,
            resource_key=form.resource_key,
        )
        data = remove_resource(
            manifest,
            collection_name=form.collection_name,
            resource_key=form.resource_key,
            collection_names=DashboardService.RESOURCE_KEYS,
        )
        reference = form.change_reference.strip()
        message = f"Day-1: Delete {form.resource_key}"
        if reference:
            message = f"[{reference}] {message}"
        result = await git.write_manifest(
            form.cloud,
            form.environment,
            form.region,
            form.resource_path,
            data,
            commit_message=message,
        )
        return _resource_mutation_result(
            request,
            action="deleted",
            result=result,
            project=form.project,
            resource_key=form.resource_key,
        )
    except RepositoryStateError as exc:
        logger.error("Repository verification failed during deletion: %s", exc, exc_info=True)
        return render_repository_state_error(request)
    except Exception as exc:
        logger.error("Error deleting resource: %s", exc, exc_info=True)
        return render_partial("partials/deploy-result.html", request, **htmx_error_context(escape(str(exc))))
