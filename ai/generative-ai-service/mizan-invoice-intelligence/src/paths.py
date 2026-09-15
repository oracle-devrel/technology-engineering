"""Small helpers for dotted paths in nested invoice payloads.

Author: Ali Ottoman
"""

from __future__ import annotations

from typing import Any


def flatten_values(value: Any, prefix: str = "") -> dict[str, Any]:
    """Flatten nested dictionaries and lists into stable dotted paths."""

    if isinstance(value, dict):
        flattened: dict[str, Any] = {}
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            flattened.update(flatten_values(child, path))
        return flattened
    if isinstance(value, list):
        flattened = {}
        for index, child in enumerate(value):
            flattened.update(flatten_values(child, f"{prefix}[{index}]"))
        return flattened
    return {prefix: value}
