"""Field-name and literal-value rendering helpers for the KQL→Logan converter.

Extracted verbatim from ``scripts/kql/_facade_impl.py`` (plan T5). Depends
only on the lookup tables in ``_constants``; everything here is a pure string
transform with no pipeline state.
"""

from __future__ import annotations

import re

from scripts.kql._constants import NUMERIC_FIELD_TYPES, STRING_FIELD_TYPES


def _escape_logan_string(value) -> str:
    """Escape a value for embedding inside a Logan QL single-quoted literal.

    Logan QL escapes an interior single quote by DOUBLING it (``''``), never
    with a backslash. The quote-doubling mirrors
    ``scripts/kql/canonical.py:_emit_qstring`` so converter output is
    ``canonical()``-stable (a stray ``\\'`` terminates the literal early and
    makes ``canonical()`` raise).

    Order of operations:

    1. Normalize any backslash-escaped quote (``\\'``) an upstream conversion
       step may have introduced back to a bare quote, so it cannot leak into
       the emitted literal as ``\\'``.
    2. Double literal backslashes (pre-existing behavior — Logan literals carry
       backslashes through verbatim; a doubled ``\\\\`` survives ``canonical()``
       because backslashes inside a quoted string are content, not escapes).
    3. Double interior single quotes per Logan QL convention.
    """
    if value is None:
        return ""
    text = str(value).replace("\\'", "'")
    return text.replace("\\", "\\\\").replace("'", "''")


def _normalize_field_name(field: str) -> str:
    return field.strip().strip("`'\" ")


def _field_is_quoted(field: str) -> bool:
    return len(field) >= 2 and field[0] == "'" and field[-1] == "'"


def _display_field_name(field: str) -> str:
    value = field.strip()
    if _field_is_quoted(value):
        return value[1:-1].replace("\\'", "'")
    return value


def _logan_field_reference(display_name: str) -> str:
    """Return a Logan field reference, quoting display fields that need it."""
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", display_name):
        return display_name
    return f"'{_escape_logan_string(display_name)}'"


def _is_allowed_logan_field(field: str, mapping: dict, allowed_aliases: set[str] | None = None) -> bool:
    display_name = _display_field_name(field)
    if allowed_aliases and display_name in allowed_aliases:
        return True
    return display_name in mapping.get("allowed_fields", set())


def _record_field_error(errors: list[str] | None, reason: str) -> None:
    if errors is not None:
        errors.append(reason)


def _field_role(field: str, mapping: dict) -> str | None:
    return mapping.get("field_roles", {}).get(_normalize_field_name(field))


def map_field(
    field: str,
    mapping: dict,
    errors: list[str] | None = None,
    allowed_aliases: set[str] | None = None,
) -> str:
    """Map a Sentinel/KQL field name into a Logan display field."""
    raw = _normalize_field_name(field)
    if raw in mapping["fields"]:
        mapped = mapping["fields"][raw]
        if mapping.get("field_specs", {}).get(raw, {}).get("parser_change_required"):
            _record_field_error(errors, f"parser_readiness:pending:{raw}")
        if not _is_allowed_logan_field(mapped, mapping, allowed_aliases):
            _record_field_error(errors, f"unsupported OCI field reference: {_display_field_name(mapped)}")
        return mapped
    if allowed_aliases and raw in allowed_aliases:
        return raw
    if raw in mapping.get("allowed_fields", set()):
        return _logan_field_reference(raw)
    if raw in {"TimeGenerated", "Timestamp"}:
        return "Time"
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", raw):
        _record_field_error(errors, f"unsupported Sentinel field mapping: {raw}")
        return raw
    _record_field_error(errors, f"unsupported Sentinel field mapping: {raw}")
    return f"'{_escape_logan_string(raw)}'"


def _format_value(value: str) -> str:
    raw = _literal_value(value)
    if raw.lower() == "null":
        return "null"
    if re.fullmatch(r"-?\d+(?:\.\d+)?", raw):
        return raw
    if raw.lower() in {"true", "false"}:
        return f"'{raw.lower()}'"
    return f"'{_escape_logan_string(raw)}'"


def _literal_value(value: str) -> str:
    raw = value.strip()
    if raw.startswith("@"):
        raw = raw[1:].strip()
    if raw.startswith("(") and raw.endswith(")"):
        raw = raw[1:-1].strip()
    if (raw.startswith("'") and raw.endswith("'")) or (raw.startswith('"') and raw.endswith('"')):
        raw = raw[1:-1]
    return raw


def _format_value_for_field(value: str, field: str, mapping: dict) -> str:
    raw = _literal_value(value)
    if raw.lower() == "null":
        return "null"
    field_type = mapping.get("field_types", {}).get(_display_field_name(field), "").upper()
    if field_type in NUMERIC_FIELD_TYPES and re.fullmatch(r"-?\d+(?:\.\d+)?", raw):
        return raw
    if field_type in STRING_FIELD_TYPES:
        if raw.lower() in {"true", "false"}:
            raw = raw.lower()
        return f"'{_escape_logan_string(raw)}'"
    return _format_value(value)


def _cleanup_boolean_expression(expression: str) -> str:
    text = re.sub(r"\bAND\b", "and", expression, flags=re.IGNORECASE)
    text = re.sub(r"\bOR\b", "or", text, flags=re.IGNORECASE)
    text = re.sub(r"\bNOT\b", "not", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"^\s*(?:and|or)\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+(?:and|or)\s*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\(\s*\)", "", text)
    text = re.sub(r"\(\s*(and|or)\s+", "(", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+(and|or)\s*\)", ")", text, flags=re.IGNORECASE)
    return text.strip()


def _remove_time_filters(predicate: str) -> str:
    text = predicate
    time_field = r"(?:TimeGenerated|Timestamp|EventCreationTime|EventEndTime|CreationTime|StartTime|EndTime)"
    time_value = r"(?:ago\([^)]*\)|datetime\([^)]*\)|now\(\)|[^\s)]+)"
    patterns = [
        rf"(?:\s*(?:and|or)\s*)?\b{time_field}\s+between\s*\((?:[^()]|\([^()]*\))*\s*\.\.\s*(?:[^()]|\([^()]*\))*\)",
        rf"(?:\s*(?:and|or)\s*)?\b{time_field}\s*(?:>=|>|<=|<|==|=~|=)\s*{time_value}",
    ]
    for pattern in patterns:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)
    return _cleanup_boolean_expression(text)
