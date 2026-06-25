"""Mapping-config and field-dictionary loaders for the KQL→Logan converter.

Extracted verbatim from ``scripts/kql/_facade_impl.py`` (plan T5).
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.kql._constants import (
    AZURE_AUDIT_SCHEMA_FIELDS,
    FIELD_DICTIONARY_PATH,
    LOGAN_BUILTIN_FIELDS,
)


def load_mapping_config(path: Path | None = None) -> dict:
    """Load Sentinel table/field mapping configuration."""
    from scripts.kql.mapping_loader import load_mapping

    payload = load_mapping(path)
    allowed_fields = set(payload.get("allowed_fields", []))
    allowed_fields.update(LOGAN_BUILTIN_FIELDS)
    allowed_fields.update(AZURE_AUDIT_SCHEMA_FIELDS)
    allowed_fields.update(_load_field_dictionary_fields())
    return {
        "tables": payload.get("tables", {}),
        "fields": payload.get("fields", {}),
        "field_roles": payload.get("field_roles", {}),
        "field_specs": payload.get("field_specs", {}),
        "allowed_fields": allowed_fields,
        "field_types": _load_field_dictionary_field_types(),
    }


def _load_field_dictionary_fields(path: Path = FIELD_DICTIONARY_PATH) -> set[str]:
    """Return OCI Log Analytics field display names from the generated dictionary."""
    if not path.exists():
        return set()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    fields = set(payload.get("approved_builtins", []))
    for field in payload.get("fields", []):
        display_name = field.get("display_name")
        if display_name:
            fields.add(display_name)
    return fields


def _load_field_dictionary_field_types(path: Path = FIELD_DICTIONARY_PATH) -> dict[str, str]:
    """Return OCI field display name to field type mappings from the generated dictionary."""
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    field_types: dict[str, str] = {}
    for field in payload.get("fields", []):
        display_name = field.get("display_name")
        field_type = field.get("type") or field.get("data_type")
        if display_name and field_type:
            field_types[display_name] = str(field_type).upper()
    return field_types
