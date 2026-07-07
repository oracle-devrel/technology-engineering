"""Pure field/parser-contract helpers for setup_log_sources (behavior-preserving extract).

These operate only on the static definitions in ``logsources.definitions`` and
plain arguments — no OCI client calls — so they live outside the orchestrator.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logsources.definitions import *  # noqa: F401,F403


def unique_preserving_order(values):
    """Return values without duplicates while preserving the first occurrence."""
    seen = set()
    result = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def field_data_type_for(display_name):
    """Return the OCI Log Analytics data type to use when creating a field."""
    return FIELD_DATA_TYPE_OVERRIDES.get(display_name, "String")


def is_single_value_string_limit_error(exc):
    """Return True when the tenancy exhausted single-valued string fields."""
    return (
        getattr(exc, "status", None) == 400
        and "single-valued string field" in str(getattr(exc, "message", "")).lower()
    )


def select_field_contract(octo_apm_only=False, application_only=False):
    """Return the field and parser contract for the requested setup scope."""
    if octo_apm_only:
        return custom_fields_for_octo_apm_workshop(), field_mappings_for_octo_apm_workshop()
    if application_only:
        return custom_fields_for_application_logs(), APP_FIELD_MAPPINGS
    return CUSTOM_FIELDS, APP_FIELD_MAPPINGS


def custom_fields_for_application_logs():
    """Return the custom fields needed by the SOC Application/Octo APM parser."""
    mapped_fields = [
        field_name
        for field_name, _json_path, _sequence in APP_FIELD_MAPPINGS
        if field_name not in {"msg", "time"}
    ]
    custom_field_set = set(CUSTOM_FIELDS)
    return [
        field_name
        for field_name in unique_preserving_order(mapped_fields)
        if field_name in custom_field_set
    ]


def custom_fields_for_octo_apm_workshop():
    """Return the minimal fields needed by the Octo APM workshop assets."""
    custom_field_set = set(CUSTOM_FIELDS)
    return [
        field_name
        for field_name in unique_preserving_order(OCTO_APM_WORKSHOP_FIELD_DISPLAY_NAMES)
        if field_name in custom_field_set
    ]


def field_mappings_for_octo_apm_workshop():
    """Return parser mappings limited to the Octo APM workshop contract."""
    allowed_fields = set(OCTO_APM_WORKSHOP_FIELD_DISPLAY_NAMES) | {"msg", "time"}
    return [
        mapping
        for mapping in APP_FIELD_MAPPINGS
        if mapping[0] in allowed_fields
    ]


def missing_octo_apm_workshop_fields(field_map):
    """Return Octo workshop fields that are unavailable for parser creation."""
    missing = []
    for display_name in OCTO_APM_WORKSHOP_FIELD_DISPLAY_NAMES:
        if display_name in field_map or display_name.lower() in field_map:
            continue
        missing.append(display_name)
    return missing


def build_field_inventory_entry(field):
    """Return the stable field metadata needed for reuse/audit decisions."""
    return {
        "display_name": getattr(field, "display_name", None),
        "name": getattr(field, "name", None),
        "data_type": getattr(field, "data_type", None),
        "is_multi_valued": getattr(field, "is_multi_valued", None),
        "is_system": getattr(field, "is_system", None),
    }


def add_field_inventory_lookup(lookup, key, entry):
    """Add exact and case-insensitive lookups without replacing the first match."""
    if not key:
        return
    lookup.setdefault(key, entry)
    lookup.setdefault(key.lower(), entry)


def find_field_by_display(inventory, display_name):
    """Return an existing field by display name, with case-insensitive fallback."""
    return (
        inventory["by_display"].get(display_name)
        or inventory["by_display"].get(display_name.lower())
    )


def find_field_by_name(inventory, field_name):
    """Return an existing field by internal name, with case-insensitive fallback."""
    return (
        inventory["by_name"].get(field_name)
        or inventory["by_name"].get(field_name.lower())
    )


def find_existing_field_for_creation(inventory, display_name):
    """Return an existing field that can satisfy this requested display name."""
    return find_field_by_display(inventory, display_name)


def field_rewrite_candidates(inventory, missing_field_names):
    """Return audit-only candidates that would require query/display rewrites."""
    candidates = []
    for display_name in missing_field_names:
        if display_name in RESERVED_PARSER_FIELD_DISPLAY_NAMES:
            continue
        for existing_display in FIELD_REWRITE_REUSE_CANDIDATES.get(display_name, ()):
            entry = find_field_by_display(inventory, existing_display)
            if not entry or not entry.get("name"):
                continue
            candidates.append({
                "requested_display_name": display_name,
                "existing_display_name": entry.get("display_name") or existing_display,
                "existing_internal_name": entry["name"],
                "query_rewrite_required": True,
            })
            break
    return candidates


def build_field_reuse_audit(inventory, field_display_names):
    """Return exact namespace reuse, missing fields, and rewrite candidates."""
    exact_reuse = []
    internal_name_reuse = []
    missing = []
    requested = unique_preserving_order(field_display_names)

    for display_name in requested:
        entry = find_field_by_display(inventory, display_name)
        if entry and entry.get("name"):
            exact_reuse.append({
                "requested_display_name": display_name,
                "existing_display_name": entry.get("display_name") or display_name,
                "existing_internal_name": entry["name"],
                "data_type": entry.get("data_type"),
            })
            continue

        entry = find_field_by_name(inventory, display_name)
        if entry and entry.get("name"):
            internal_name_reuse.append({
                "requested_display_name": display_name,
                "existing_display_name": entry.get("display_name"),
                "existing_internal_name": entry["name"],
                "data_type": entry.get("data_type"),
            })

        missing.append(display_name)

    return {
        "total_requested": len(requested),
        "exact_reuse": exact_reuse,
        "internal_name_reuse": internal_name_reuse,
        "missing": missing,
        "rewrite_candidates": field_rewrite_candidates(inventory, missing),
    }


def print_field_reuse_audit(audit, show_exact=False):
    """Print a namespace field audit without tenancy-specific identifiers."""
    exact_count = len(audit["exact_reuse"])
    internal_count = len(audit["internal_name_reuse"])
    missing_count = len(audit["missing"])
    total = audit["total_requested"]

    print("FIELD AUDIT - namespace existing-field reuse")
    print(f"  Requested parser fields: {total}")
    print(f"  Exact display-name fields reused: {exact_count}")
    print(f"  Internal-name matches found: {internal_count}")
    print(f"  Fields that setup would create: {missing_count}")

    if show_exact and audit["exact_reuse"]:
        print("\n  Exact display-name reuse:")
        for row in audit["exact_reuse"]:
            data_type = row.get("data_type") or "unknown"
            print(
                "    - "
                f"{row['requested_display_name']} -> {row['existing_internal_name']} "
                f"({data_type})"
            )

    if audit["internal_name_reuse"]:
        print("\n  Internal-name matches requiring display-name review:")
        for row in audit["internal_name_reuse"]:
            display = row.get("existing_display_name") or row["requested_display_name"]
            print(
                "    - "
                f"{row['requested_display_name']} -> {row['existing_internal_name']} "
                f"(display: {display})"
            )

    if audit["missing"]:
        print("\n  Fields to create if setup runs:")
        for display_name in audit["missing"]:
            print(f"    - {display_name} ({field_data_type_for(display_name)})")

    if audit["rewrite_candidates"]:
        print("\n  Existing-field rewrite candidates, not applied automatically:")
        for row in audit["rewrite_candidates"]:
            print(
                "    - "
                f"{row['requested_display_name']} could reuse "
                f"{row['existing_display_name']} after query/dashboard rewrites"
            )
