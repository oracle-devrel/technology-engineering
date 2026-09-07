"""Shared helpers for HTMX form parsing and Pydantic validation messages."""
from __future__ import annotations

from typing import Any, Mapping

from fastapi import Request
from pydantic import ValidationError

_VALUE_ERROR_PREFIX = "Value error, "
_REQUIRED_ERROR_TYPES = {"missing", "string_too_short", "string_type"}

def normalize_form_value(value: Any) -> Any:
    """Normalize HTMX list/None values to scalar strings."""
    if isinstance(value, list):
        return value[0] if value else ""
    if value is None:
        return ""
    return value


def build_form_payload(
    form_data: Mapping[str, Any],
    *,
    defaults: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Convert Starlette form data into a normalized dictionary."""
    payload = {key: normalize_form_value(value) for key, value in form_data.items()}

    for key, default_value in (defaults or {}).items():
        if payload.get(key) in {"", None}:
            payload[key] = default_value

    return payload


async def request_form_payload(
    request: Request,
    *,
    defaults: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build normalized payload directly from request form data."""
    return build_form_payload(await request.form(), defaults=defaults)


def validation_messages(
    exc: ValidationError,
    *,
    required_labels: Mapping[str, str] | None = None,
    custom_errors: Mapping[tuple[str, str], str] | None = None,
    default_message: str = "Invalid form input",
    strip_value_error_prefix: bool = True,
) -> list[str]:
    """Normalize Pydantic errors into concise, deduplicated UI messages."""
    required_labels = required_labels or {}
    custom_errors = custom_errors or {}
    messages: list[str] = []

    for err in exc.errors():
        loc = ".".join(str(part) for part in err.get("loc", []))
        err_type = err.get("type", "")

        if (loc, err_type) in custom_errors:
            message = custom_errors[(loc, err_type)]
        elif (loc, "*") in custom_errors:
            message = custom_errors[(loc, "*")]
        elif loc and err_type in _REQUIRED_ERROR_TYPES:
            label = required_labels.get(loc) or loc.replace("_", " ")
            label = label[:1].upper() + label[1:]
            message = f"{label} is required"
        else:
            message = err.get("msg", default_message)

        if strip_value_error_prefix and message.startswith(_VALUE_ERROR_PREFIX):
            message = message.replace(_VALUE_ERROR_PREFIX, "", 1)

        if message not in messages:
            messages.append(message)

    return messages


def htmx_error_context(error: str, *, project: str | None = None) -> dict[str, Any]:
    """Build a consistent template context for HTMX error partials."""
    context: dict[str, Any] = {"success": False, "error": error}
    if project is not None:
        context["project"] = project
    return context
