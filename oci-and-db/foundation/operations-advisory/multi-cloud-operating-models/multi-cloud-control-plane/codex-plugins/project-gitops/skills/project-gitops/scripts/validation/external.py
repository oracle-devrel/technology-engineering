"""Azure and Google Cloud manifest validation."""

from __future__ import annotations

import json
from typing import Any

from .common import UNRESOLVED_TOKEN_RE, failure

_failure = failure
_UNRESOLVED_TOKEN_RE = UNRESOLVED_TOKEN_RE


def _handoff_references(markdown: str, cloud: str) -> dict[str, str]:
    """Return labeled references from only the selected cloud handoff section."""
    heading = "azure" if cloud == "azure" else "gcp"
    references: dict[str, str] = {}
    active = False
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            headings = {heading}
            if cloud == "gcp":
                headings.update({"google", "google cloud"})
            active = line[3:].strip().casefold() in headings
            continue
        if not active or not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if (
            len(cells) >= 2
            and cells[0].casefold() not in {"reference", "---"}
            and cells[1]
            and set(cells[1]) != {"-"}
        ):
            label = cells[0].casefold()
            if label in references:
                failure("INVALID_HANDOFF", "The selected cloud handoff has duplicate references.")
            references[label] = cells[1]
    if not references:
        failure("INVALID_HANDOFF", "The selected cloud handoff section is missing.")
    return references


def validate_external_manifest(
    cloud: str, kind: str, environment: str, document: object, handoff_markdown: str
) -> str:
    """Validate one Azure or Google Cloud manifest against its handoff section."""
    if cloud not in {"azure", "gcp"} or kind not in {"compute", "adb"}:
        failure("UNSUPPORTED_CLOUD", "The requested cloud or workload is unsupported.")
    if document == {}:
        return "delete"
    if not isinstance(document, dict):
        _failure("INVALID_MANIFEST", "The workload manifest must be an object.")
    root = {
        ("azure", "compute"): "virtual_machines",
        ("azure", "adb"): "oracle_autonomous_databases",
        ("gcp", "compute"): "gcp_virtual_machines_configuration",
        ("gcp", "adb"): "gcp_autonomous_databases_configuration",
    }[(cloud, kind)]
    allowed_roots = {root} | ({"project_id"} if cloud == "gcp" else set())
    resources = document.get(root)
    if set(document) != allowed_roots or not isinstance(resources, dict) or not resources:
        _failure("INVALID_MANIFEST", "The workload manifest root is invalid.")
    required = {
        ("azure", "compute"): {"name", "location", "resource_group_name", "subnet_id", "network_security_group_id", "size", "admin_username", "ssh_public_key"},
        ("azure", "adb"): {"name", "location", "resource_group_name", "subnet_id", "virtual_network_id", "admin_password"},
        ("gcp", "compute"): {"name", "zone", "subnetwork", "service_account", "ssh_public_key"},
        ("gcp", "adb"): {"autonomous_database_id", "display_name", "database", "odb_network", "odb_subnet", "properties"},
    }[(cloud, kind)]
    handoff_references = _handoff_references(handoff_markdown, cloud)
    reference_fields = {
        ("azure", "compute"): {"location": "region", "resource_group_name": "resource group", "subnet_id": "vm subnet id", "network_security_group_id": "nsg id"},
        ("azure", "adb"): {"location": "region", "resource_group_name": "resource group", "subnet_id": "adb subnet id", "virtual_network_id": "vnet id"},
        ("gcp", "compute"): {"zone": "zone", "subnetwork": "subnetwork", "service_account": "service account"},
        ("gcp", "adb"): {"odb_network": "odb network id", "odb_subnet": "odb subnet id"},
    }[(cloud, kind)]
    required_handoff_labels = set(reference_fields.values())
    required_handoff_labels.add("subscription id" if cloud == "azure" else "project id")
    if not required_handoff_labels.issubset(handoff_references):
        _failure("INVALID_HANDOFF", "The selected cloud handoff is incomplete.")
    if cloud == "gcp" and document.get("project_id") != handoff_references["project id"]:
        _failure("HANDOFF_MISMATCH", "The Google project does not match the handoff.")
    for resource_document in resources.values():
        if not isinstance(resource_document, dict) or not required.issubset(resource_document):
            _failure("INVALID_MANIFEST", "A workload declaration is incomplete.")
        if any("public_ip" in key.casefold() for key in resource_document):
            _failure("PUBLIC_IP_FORBIDDEN", "Public IP fields are not supported.")
        if any(resource_document[field] != handoff_references[label] for field, label in reference_fields.items()):
            _failure("HANDOFF_MISMATCH", "A workload reference does not match the handoff.")
        if cloud == "azure":
            prefix = f"/subscriptions/{handoff_references['subscription id']}/"
            id_fields = {"subnet_id", "network_security_group_id", "virtual_network_id"}.intersection(reference_fields)
            if any(not resource_document[field].startswith(prefix) for field in id_fields):
                _failure("HANDOFF_MISMATCH", "An Azure resource ID uses another subscription.")
        if cloud == "gcp" and kind == "adb":
            properties = resource_document.get("properties")
            if not isinstance(properties, dict) or properties.get("secret_id") != handoff_references.get("password secret"):
                _failure("HANDOFF_MISMATCH", "The password secret does not match the handoff.")
    expected_prefix = f"__{environment.upper()}_"
    for token in _UNRESOLVED_TOKEN_RE.findall(json.dumps(document, sort_keys=True)):
        if not token.startswith(expected_prefix):
            _failure("CROSS_ENVIRONMENT_SECRET", "A secret placeholder belongs to another environment.")
    return "upsert"


def _external_resource_entries(cloud: str, kind: str, document: object) -> tuple[dict[str, object], object]:
    if document == {}:
        return {}, None
    if not isinstance(document, dict):
        _failure("INVALID_MANIFEST", "The workload manifest must be an object.")
    root = {
        ("azure", "compute"): "virtual_machines",
        ("azure", "adb"): "oracle_autonomous_databases",
        ("gcp", "compute"): "gcp_virtual_machines_configuration",
        ("gcp", "adb"): "gcp_autonomous_databases_configuration",
    }.get((cloud, kind))
    if root is None:
        _failure("UNSUPPORTED_CLOUD", "The requested cloud or workload is unsupported.")
    allowed_roots = {root} | ({"project_id"} if cloud == "gcp" else set())
    entries = document.get(root)
    if set(document) != allowed_roots or not isinstance(entries, dict) or not entries:
        _failure("INVALID_MANIFEST", "The workload manifest root is invalid.")
    return entries, document.get("project_id")


def validate_external_change(cloud: str, kind: str, environment: str, base_document: object, candidate_document: object, handoff_markdown: str) -> str:
    """Validate exactly one Azure or Google Cloud aggregate resource mutation."""
    base_entries, base_project = _external_resource_entries(cloud, kind, base_document)
    candidate_entries, candidate_project = _external_resource_entries(cloud, kind, candidate_document)
    if cloud == "gcp" and base_entries and candidate_entries and base_project != candidate_project:
        _failure("INVALID_CHANGE", "The Google project scope cannot change.")
    created = set(candidate_entries) - set(base_entries)
    deleted = set(base_entries) - set(candidate_entries)
    updated = {key for key in set(base_entries).intersection(candidate_entries) if base_entries[key] != candidate_entries[key]}
    if len(created) + len(deleted) + len(updated) != 1:
        _failure("INVALID_CHANGE", "Exactly one workload resource must be changed.")
    action = "create" if created else "delete" if deleted else "update"
    validate_external_manifest(cloud, kind, environment, candidate_document if candidate_entries else base_document, handoff_markdown)
    return action
