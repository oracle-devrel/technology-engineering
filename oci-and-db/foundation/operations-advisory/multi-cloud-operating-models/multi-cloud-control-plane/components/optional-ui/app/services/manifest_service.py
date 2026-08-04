"""Safe, generic updates to aggregate Terraform resource manifests."""
from copy import deepcopy
from typing import Any


class ManifestError(ValueError):
    """Raised when a manifest cannot identify one resource unambiguously."""


def _resource_collections(
    node: Any,
    collection_name: str,
) -> list[dict[str, Any]]:
    """Return maps named ``collection_name`` at any depth in a manifest."""
    matches: list[dict[str, Any]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key == collection_name and isinstance(value, dict):
                matches.append(value)
            matches.extend(_resource_collections(value, collection_name))
    elif isinstance(node, list):
        for value in node:
            matches.extend(_resource_collections(value, collection_name))
    return matches


def _target_collection(
    manifest: dict[str, Any],
    collection_name: str,
    resource_key: str,
) -> dict[str, Any]:
    """Find exactly one collection containing a requested resource entry."""
    matches = [
        collection
        for collection in _resource_collections(manifest, collection_name)
        if resource_key in collection
    ]
    if not matches:
        raise ManifestError(
            f"Resource '{resource_key}' was not found in '{collection_name}'"
        )
    if len(matches) > 1:
        raise ManifestError(
            f"Resource '{resource_key}' appears in multiple '{collection_name}' maps"
        )
    return matches[0]


def replace_resource(
    manifest: dict[str, Any],
    *,
    collection_name: str,
    resource_key: str,
    replacement: dict[str, Any],
) -> dict[str, Any]:
    """Replace one resource map entry without changing its siblings."""
    updated = deepcopy(manifest)
    collection = _target_collection(updated, collection_name, resource_key)
    collection[resource_key] = deepcopy(replacement)
    return updated


def get_resource(
    manifest: dict[str, Any],
    *,
    collection_name: str,
    resource_key: str,
) -> dict[str, Any]:
    """Return a detached resource entry after unambiguous lookup."""
    resource = _target_collection(manifest, collection_name, resource_key)[resource_key]
    if not isinstance(resource, dict):
        raise ManifestError(
            f"Resource '{resource_key}' in '{collection_name}' is not an object"
        )
    return deepcopy(resource)


def remove_resource(
    manifest: dict[str, Any],
    *,
    collection_name: str,
    resource_key: str,
    collection_names: set[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Remove one resource map entry, using ``{}`` for a now-empty manifest."""
    updated = deepcopy(manifest)
    collection = _target_collection(updated, collection_name, resource_key)
    del collection[resource_key]
    if not collection:
        if collection_names and _has_remaining_resource_entries(
            updated,
            set(collection_names),
        ):
            return updated
        return {}
    return updated


def _has_remaining_resource_entries(node: Any, collection_names: set[str]) -> bool:
    """Return whether a known resource map still has at least one entry."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key in collection_names and isinstance(value, dict) and value:
                return True
            if _has_remaining_resource_entries(value, collection_names):
                return True
    elif isinstance(node, list):
        return any(_has_remaining_resource_entries(value, collection_names) for value in node)
    return False
