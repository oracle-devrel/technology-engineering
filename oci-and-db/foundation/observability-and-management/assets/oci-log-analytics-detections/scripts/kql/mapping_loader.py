"""Strict Sentinel-to-Logan mapping loader.

The sharded ``config/mapping`` tree is the authoritative editing surface.
``config/sentinel_oci_mapping.yaml`` remains a generated compatibility
re-export for older tooling and explicit-path callers.
"""

from __future__ import annotations

import itertools
from pathlib import Path
from typing import Any

import yaml

PROJECT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_ROOT_PATH = PROJECT_DIR / "config" / "mapping" / "_root.yaml"
DEFAULT_COMPAT_PATH = PROJECT_DIR / "config" / "sentinel_oci_mapping.yaml"

ALLOWED_FIELD_ROLES = frozenset(
    {"subject", "target", "initiator", "resource", "time", "hash", "network"}
)


class MappingConfigError(ValueError):
    """Raised when a mapping file is structurally invalid."""


class StrictSafeLoader(yaml.SafeLoader):
    """PyYAML loader that rejects duplicate keys in every mapping node."""

    source_path = "<stream>"


def _construct_mapping(loader: StrictSafeLoader, node, deep: bool = False) -> dict:
    loader.flatten_mapping(node)
    values: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in values:
            path = getattr(loader, "source_path", "<stream>")
            raise MappingConfigError(f"duplicate_key:{path}:{key}")
        values[key] = loader.construct_object(value_node, deep=deep)
    return values


StrictSafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping,
)


def load_yaml_strict(path: str | Path) -> dict:
    """Load one YAML file and fail on duplicate keys."""

    yaml_path = Path(path)
    with yaml_path.open(encoding="utf-8") as handle:
        loader = StrictSafeLoader(handle)
        loader.source_path = str(yaml_path)
        try:
            payload = loader.get_single_data()
        finally:
            loader.dispose()
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise MappingConfigError(f"invalid_mapping:{yaml_path}:expected_object")
    return payload


def _resolve_shard_path(root_path: Path, shard: str | Path) -> Path:
    shard_path = Path(shard)
    if shard_path.is_absolute():
        return shard_path
    return root_path.parent / shard_path


def _read_shard_list(root_payload: dict, preferred: str, legacy: str) -> list[str]:
    shards = root_payload.get(preferred, root_payload.get(legacy, []))
    if not isinstance(shards, list) or not all(isinstance(item, str) for item in shards):
        raise MappingConfigError(f"invalid_mapping:_root:{preferred}:expected_string_list")
    return shards


def _merge_section(
    root_path: Path,
    root_payload: dict,
    section: str,
    shard_key: str,
    legacy_shard_key: str,
) -> dict:
    merged: dict = {}
    for shard in _read_shard_list(root_payload, shard_key, legacy_shard_key):
        shard_path = _resolve_shard_path(root_path, shard)
        payload = load_yaml_strict(shard_path)
        entries = payload.get(section, {})
        if not isinstance(entries, dict):
            raise MappingConfigError(f"invalid_mapping:{shard_path}:{section}:expected_object")
        for key, value in entries.items():
            if key in merged:
                raise MappingConfigError(f"duplicate_key:{shard_path}:{section}.{key}")
            merged[key] = value
    return merged


def _normalize_field_spec(field: str, value: Any, field_roles: dict[str, str] | None = None) -> dict[str, str]:
    if isinstance(value, str):
        role = (field_roles or {}).get(field)
        if not role:
            raise MappingConfigError(f"missing_role:{field}")
        spec = {"target": value, "role": role}
    elif isinstance(value, dict):
        target = value.get("target")
        role = value.get("role")
        if not isinstance(target, str) or not target:
            raise MappingConfigError(f"invalid_field_mapping:{field}:target")
        if not isinstance(role, str) or not role:
            raise MappingConfigError(f"missing_role:{field}")
        spec = {"target": target, "role": role}
        if value.get("parser_change_required") is not None:
            spec["parser_change_required"] = bool(value["parser_change_required"])
    else:
        raise MappingConfigError(f"invalid_field_mapping:{field}:expected_string_or_object")

    if spec["role"] not in ALLOWED_FIELD_ROLES:
        raise MappingConfigError(f"invalid_role:{field}:{spec['role']}")
    return spec


def _normalize_payload(payload: dict) -> dict:
    tables = payload.get("tables", {})
    fields = payload.get("fields", {})
    if not isinstance(tables, dict):
        raise MappingConfigError("invalid_mapping:tables:expected_object")
    if not isinstance(fields, dict):
        raise MappingConfigError("invalid_mapping:fields:expected_object")

    field_roles = payload.get("field_roles", {})
    if field_roles is None:
        field_roles = {}
    if not isinstance(field_roles, dict):
        raise MappingConfigError("invalid_mapping:field_roles:expected_object")

    field_specs = {
        field: _normalize_field_spec(field, value, field_roles)
        for field, value in fields.items()
    }
    legacy_fields = {field: spec["target"] for field, spec in field_specs.items()}
    roles = {field: spec["role"] for field, spec in field_specs.items()}
    return {
        "tables": tables,
        "fields": legacy_fields,
        "field_roles": roles,
        "field_specs": field_specs,
    }


def load_sharded_mapping(root_path: str | Path = DEFAULT_ROOT_PATH) -> dict:
    """Load and merge mapping shards rooted at ``_root.yaml``."""

    root = Path(root_path)
    root_payload = load_yaml_strict(root)
    tables = _merge_section(root, root_payload, "tables", "table_shards", "tables")
    fields = _merge_section(root, root_payload, "fields", "field_shards", "fields")
    return _normalize_payload({"tables": tables, "fields": fields})


def load_compat_mapping(path: str | Path = DEFAULT_COMPAT_PATH) -> dict:
    """Load a monolithic compatibility mapping with strict duplicate checks."""

    return _normalize_payload(load_yaml_strict(path))


def load_mapping(path: str | Path | None = None) -> dict:
    """Load the mapping, preferring shards unless an explicit path is provided."""

    if path is None:
        if DEFAULT_ROOT_PATH.exists():
            return load_sharded_mapping(DEFAULT_ROOT_PATH)
        return load_compat_mapping(DEFAULT_COMPAT_PATH)

    mapping_path = Path(path)
    if mapping_path.name == "_root.yaml":
        return load_sharded_mapping(mapping_path)
    return load_compat_mapping(mapping_path)


def compatibility_payload(mapping: dict) -> dict:
    """Return the legacy monolithic mapping schema plus role sidecar."""

    return {
        "tables": mapping.get("tables", {}),
        "fields": mapping.get("fields", {}),
        "field_roles": mapping.get("field_roles", {}),
    }


def write_compat_mapping(
    output_path: str | Path = DEFAULT_COMPAT_PATH,
    mapping: dict | None = None,
) -> Path:
    """Write the generated compatibility mapping file."""

    payload = compatibility_payload(mapping or load_mapping())
    text = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
    header = (
        "# Generated from config/mapping/*.yaml. Do not edit by hand.\n"
        "# Run: python3 scripts/generate_mapping_config.py --export-compat\n\n"
    )
    path = Path(output_path)
    path.write_text(header + text, encoding="utf-8")
    return path


def _display_target(target: str) -> str:
    value = target.strip()
    if len(value) >= 2 and value[0] == "'" and value[-1] == "'":
        return value[1:-1].replace("\\'", "'")
    return value


def build_collision_report(mapping: dict) -> dict:
    """Build a deterministic many-to-one mapping collision report."""

    by_target: dict[str, list[str]] = {}
    for field, target in mapping.get("fields", {}).items():
        by_target.setdefault(target, []).append(field)

    collisions = []
    for target, fields in sorted(by_target.items(), key=lambda item: _display_target(item[0]).lower()):
        sorted_fields = sorted(fields)
        if len(sorted_fields) < 2:
            continue
        display_target = _display_target(target)
        reasons = [
            f"lossy_mapping_collision:{left}+{right}→{display_target}"
            for left, right in itertools.combinations(sorted_fields, 2)
        ]
        collisions.append(
            {
                "target": display_target,
                "target_mapping": target,
                "fields": sorted_fields,
                "roles": {
                    field: mapping.get("field_roles", {}).get(field, "resource")
                    for field in sorted_fields
                },
                "reasons": reasons,
            }
        )

    return {
        "version": 1,
        "generated_from": "config/mapping/_root.yaml",
        "summary": {
            "field_count": len(mapping.get("fields", {})),
            "collision_count": len(collisions),
            "collision_field_count": sum(len(item["fields"]) for item in collisions),
        },
        "collisions": collisions,
    }


__all__ = [
    "ALLOWED_FIELD_ROLES",
    "DEFAULT_COMPAT_PATH",
    "DEFAULT_ROOT_PATH",
    "MappingConfigError",
    "build_collision_report",
    "compatibility_payload",
    "load_compat_mapping",
    "load_mapping",
    "load_sharded_mapping",
    "load_yaml_strict",
    "write_compat_mapping",
]
