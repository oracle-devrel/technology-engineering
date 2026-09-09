"""OCI Autonomous Database change validation."""

from __future__ import annotations

from typing import Any, Sequence

from .common import (
    ADB_FIELDS, ADB_KEY_RE, ADB_NSG_RE, ADB_PASSWORD_RE, ADB_STRING_PATTERNS,
    ADB_VALIDATIONS, MAX_ADB_MUTATIONS, MAX_NSG_IDS, RepositoryChange, failure,
    has_sensitive_value, strict_json, success_document, valid_ocid,
    validate_workload_compartment,
)

_failure = failure
_has_sensitive_value = has_sensitive_value
_success_document = success_document
_valid_ocid = valid_ocid


def validate_adb_declaration(
    adb_key: object,
    adb: object,
    *,
    project: str,
    environment: str,
    region: str,
) -> None:
    """Validate one created or updated ADB declaration."""
    if (not isinstance(adb_key, str) or ADB_KEY_RE.fullmatch(adb_key) is None
            or not isinstance(adb, dict) or set(adb) != ADB_FIELDS):
        _failure("INVALID_ADB_CHANGE", "The ADB declaration is invalid.")
    invalid = any(type(adb[field]) is not str or pattern.fullmatch(adb[field]) is None
                  for field, pattern in ADB_STRING_PATTERNS.items())
    invalid |= any(type(adb[field]) is not bool for field in (
        "is_dedicated", "enable_cpu_auto_scaling", "enable_storage_auto_scaling",
    ))
    invalid |= adb["is_dedicated"] is not False
    invalid |= type(adb["ecpu_count"]) is not int or not 2 <= adb["ecpu_count"] <= 512
    invalid |= (type(adb["non_dw_storage_size_in_gbs"]) is not int
                or adb["non_dw_storage_size_in_gbs"] < 20)
    for field, allowed in {
        "db_workload": {"OLTP"},
        "license_model": {"BRING_YOUR_OWN_LICENSE", "LICENSE_INCLUDED"},
    }.items():
        invalid |= type(adb[field]) is not str or adb[field] not in allowed
    networking = adb["networking"]
    invalid |= not isinstance(networking, dict) or set(networking) != {
        "enable_private_endpoint", "subnet_id", "network_security_groups"
    }
    if isinstance(networking, dict):
        nsg_ids = networking.get("network_security_groups")
        invalid |= networking.get("enable_private_endpoint") is not True
        invalid |= not _valid_ocid(networking.get("subnet_id"), "subnet", region)
        invalid |= (type(nsg_ids) is not list or not 1 <= len(nsg_ids) <= MAX_NSG_IDS
                    or any(type(item) is not str or ADB_NSG_RE.fullmatch(item) is None
                           for item in nsg_ids) or len(set(nsg_ids)) != len(nsg_ids))
    if invalid:
        _failure("INVALID_ADB_CHANGE", "The ADB declaration is invalid.")
    password = adb["admin_password"]
    if type(password) is not str:
        _failure("INVALID_ADB_CHANGE", "The ADB declaration is invalid.")
    inner_secret_name = password[2:-2]
    environment_prefix = f"{environment.upper()}_"
    if (ADB_PASSWORD_RE.fullmatch(password) is None
            or "__" in inner_secret_name
            or not inner_secret_name.startswith(environment_prefix)):
        _failure("INVALID_SECRET_PLACEHOLDER",
                 "The ADB administrator secret placeholder is invalid.")


def _adb_configuration(document: object) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(document, dict) or set(document) != {"autonomous_databases_configuration"}:
        _failure("INVALID_ADB_CHANGE", "The ADB manifest is invalid.")
    configuration = document.get("autonomous_databases_configuration")
    databases = configuration.get("databases") if isinstance(configuration, dict) else None
    if not isinstance(configuration, dict) or not isinstance(databases, dict):
        _failure("INVALID_ADB_CHANGE", "The ADB manifest is invalid.")
    return configuration, databases


def _adb_aggregate(document: object, *, allow_empty: bool) -> tuple[str | None, dict[str, Any]]:
    if allow_empty and document == {}:
        return None, {}
    configuration, databases = _adb_configuration(document)
    if (set(configuration) != {"default_compartment_id", "databases"}
            or not _valid_ocid(configuration.get("default_compartment_id"), "compartment")):
        _failure("INVALID_ADB_CHANGE", "The ADB manifest is invalid.")
    return configuration["default_compartment_id"], databases


def _adb_summary(
    adb_key: str,
    adb: object,
    *,
    action: str,
    region: str,
    default_compartment_id: str | None,
    changed_fields: Sequence[str] = (),
) -> dict[str, object]:
    """Build a secret-safe summary for one ADB mutation."""
    entry = adb if isinstance(adb, dict) else {}
    summary: dict[str, object] = {
        "resource_type": "oci-adb",
        "action": action,
        "key": adb_key,
        "display_name": entry.get("display_name", adb_key),
        "db_name": entry.get("db_name"),
        "region": region,
    }
    if action == "delete":
        summary["destructive"] = True
        return summary
    summary.update({
        "compartment_id": default_compartment_id,
        "dedicated": entry.get("is_dedicated"),
        "ecpu_count": entry.get("ecpu_count"),
        "non_dw_storage_size_in_gbs": entry.get("non_dw_storage_size_in_gbs"),
        "db_workload": entry.get("db_workload"),
        "license_model": entry.get("license_model"),
        "compute_auto_scaling": entry.get("enable_cpu_auto_scaling"),
        "storage_auto_scaling": entry.get("enable_storage_auto_scaling"),
        "private_endpoint": (entry.get("networking") or {}).get("enable_private_endpoint"),
        "subnet_id": (entry.get("networking") or {}).get("subnet_id"),
        "nsg_keys": (entry.get("networking") or {}).get("network_security_groups"),
    })
    password = entry.get("admin_password")
    if isinstance(password, str) and ADB_PASSWORD_RE.fullmatch(password):
        summary["admin_password_secret_name"] = password[2:-2]
    if changed_fields:
        summary["changed_fields"] = list(changed_fields)
        summary["replacement_possible"] = True
    return summary


def validate_adb_change(change: RepositoryChange) -> dict[str, object]:
    """Validate one to three governed ADB creates, updates, or deletions."""
    base_document = strict_json(change.base_content)
    candidate_document = strict_json(change.candidate_content)
    base_default, base_databases = _adb_aggregate(base_document, allow_empty=True)
    candidate_default, candidate_databases = _adb_aggregate(candidate_document, allow_empty=True)
    for compartment_id in (base_default, candidate_default):
        if compartment_id is not None:
            validate_workload_compartment(
                change.workload_compartments, "database", compartment_id
            )
    added_keys = candidate_databases.keys() - base_databases.keys()
    removed_keys = base_databases.keys() - candidate_databases.keys()
    modified_keys = {
        key for key in base_databases.keys() & candidate_databases.keys()
        if base_databases[key] != candidate_databases[key]
    }
    mutation_count = len(added_keys) + len(removed_keys) + len(modified_keys)
    if (not 1 <= mutation_count <= MAX_ADB_MUTATIONS
            or (candidate_default is not None
                and base_default is not None
                and base_default != candidate_default)):
        _failure(
            "INVALID_ADB_CHANGE",
            "Between one and three ADBs must be created, updated, or deleted.",
        )
    for field in ("db_name", "display_name", "admin_password"):
        identities = [
            value[field].casefold()
            for value in candidate_databases.values()
            if isinstance(value, dict) and type(value.get(field)) is str
        ]
        if len(identities) != len(set(identities)):
            _failure("INVALID_ADB_CHANGE", "ADB identities and secret names must be unique.")
    resource_summaries: list[dict[str, object]] = []
    for adb_key in sorted(added_keys):
        new_adb = candidate_databases[adb_key]
        if _has_sensitive_value(new_adb):
            _failure("INVALID_SECRET_VALUE", "The ADB manifest contains a rejected value.")
        validate_adb_declaration(adb_key, new_adb, project=change.project,
                                 environment=change.environment, region=change.region)
        resource_summaries.append(_adb_summary(
            adb_key, new_adb, action="create", region=change.region,
            default_compartment_id=candidate_default,
        ))
    for adb_key in sorted(modified_keys):
        updated_adb = candidate_databases[adb_key]
        if _has_sensitive_value(updated_adb):
            _failure("INVALID_SECRET_VALUE", "The ADB manifest contains a rejected value.")
        validate_adb_declaration(adb_key, updated_adb, project=change.project,
                                 environment=change.environment, region=change.region)
        previous_adb = base_databases[adb_key]
        changed_fields = sorted(
            field for field in ADB_FIELDS
            if not isinstance(previous_adb, dict)
            or previous_adb.get(field) != updated_adb.get(field)
        )
        resource_summaries.append(_adb_summary(
            adb_key, updated_adb, action="update", region=change.region,
            default_compartment_id=candidate_default, changed_fields=changed_fields,
        ))
    for adb_key in sorted(removed_keys):
        resource_summaries.append(_adb_summary(
            adb_key, base_databases[adb_key], action="delete", region=change.region,
            default_compartment_id=base_default,
        ))
    summary: dict[str, object]
    if len(resource_summaries) == 1:
        summary = resource_summaries[0]
    else:
        actions = {resource["action"] for resource in resource_summaries}
        summary = {
            "resource_type": "oci-adb-batch",
            "action": next(iter(actions)) if len(actions) == 1 else "mixed",
            "resource_count": len(resource_summaries),
            "region": change.region,
            "destructive": any(resource.get("destructive") is True
                               for resource in resource_summaries),
            "resources": resource_summaries,
        }
    operation = f"adb-{summary['action']}" if summary["action"] != "mixed" else "adb-change"
    return _success_document(change, operation, ADB_VALIDATIONS, summary)
