"""Offline (local) safety validation for generated Logan QL queries.

Extracted verbatim from ``scripts/kql/_facade_impl.py`` (plan T5).
"""

from __future__ import annotations

import re

from scripts.kql._constants import LOGAN_COMMANDS, LOGAN_UNSUPPORTED_PATTERNS
from scripts.kql._mapping_config import load_mapping_config
from scripts.kql._text_utils import (
    _split_top_level,
    _strip_single_quoted_literals,
    _strip_string_literals,
)


def _iter_quoted_values(text: str):
    in_quote = False
    escaped = False
    start = 0
    value: list[str] = []
    for index, char in enumerate(text):
        if escaped:
            value.append(char)
            escaped = False
            continue
        if char == "\\" and in_quote:
            escaped = True
            value.append(char)
            continue
        if char == "'":
            if in_quote:
                yield "".join(value), start, index + 1
                in_quote = False
                value = []
            else:
                in_quote = True
                start = index
                value = []
            continue
        if in_quote:
            value.append(char)


def _quote_context_indicates_field(query: str, start: int, end: int) -> bool:
    after = query[end:]
    before = query[:start]
    if re.match(r"\s*(?:=|!=|>=|<=|>|<|\blike\b|\bnot\s+like\b|\bin\b|\bnot\s+in\b|\bis\b)", after, re.IGNORECASE):
        return True
    tail = before[-48:].lower()
    return bool(re.search(r"\b(?:distinctcount|unique|count|sum|max|min|avg|average)\s*\($", tail))


def _extract_query_field_references(query: str) -> set[str]:
    fields: set[str] = set()
    for value, start, end in _iter_quoted_values(query):
        if _quote_context_indicates_field(query, start, end):
            fields.add(value)
    for by_match in re.finditer(
        r"\|\s*(?:stats|eventstats|timestats|link)[^|]*\bby\b(?P<clause>[^|]+)",
        query,
        flags=re.IGNORECASE,
    ):
        fields.update(value for value, _start, _end in _iter_quoted_values(by_match.group("clause")))
    for fields_match in re.finditer(r"\|\s*fields\s+(?P<clause>[^|]+)", query, flags=re.IGNORECASE):
        fields.update(value for value, _start, _end in _iter_quoted_values(fields_match.group("clause")))
    return fields


def _extract_query_aliases(query: str) -> set[str]:
    aliases = set(re.findall(r"\bas\s+([A-Za-z_][A-Za-z0-9_]*)\b", query, flags=re.IGNORECASE))
    aliases.update(re.findall(r"\|\s*eval\s+([A-Za-z_][A-Za-z0-9_]*)\s*=", query, flags=re.IGNORECASE))
    return aliases


def _extract_unquoted_operator_fields(query: str) -> set[str]:
    stripped = _strip_string_literals(query)
    fields: set[str] = set()
    pattern = re.compile(
        r"(?<!['\"])\b(?P<field>[A-Za-z_][A-Za-z0-9_]*)\s*(?:=|!=|>=|<=|>|<|\blike\b|\bnot\s+like\b|\bin\b|\bnot\s+in\b|\bis\b)",
        re.IGNORECASE,
    )
    for match in pattern.finditer(stripped):
        field = match.group("field")
        if field.lower() not in LOGAN_COMMANDS:
            fields.add(field)
    return fields


def validate_logan_query_local(query: str, mapping: dict | None = None) -> list[str]:
    """Run offline safety checks for generated Logan QL."""
    errors = []
    if not query or not query.strip():
        return ["empty Logan query"]
    mapping = mapping or load_mapping_config()
    if query.count("'") % 2 != 0:
        errors.append("unbalanced single quotes")
    if "'Log Source'" not in query:
        errors.append("missing Logan Log Source filter")
    if re.search(r"\{\{|\}\}", query):
        errors.append("query contains unresolved placeholder braces")
    if re.search(r"\b(?:GOES HERE|REPLACE_ME|CHANGE_ME|INSERT_HERE|YOUR_VALUE)\b", query, re.IGNORECASE):
        errors.append("query contains unresolved placeholder text")
    outside_string_literals = _strip_single_quoted_literals(query)
    if '"' in outside_string_literals:
        errors.append("query contains unsafe double quote outside Logan string literal")
    if ";" in outside_string_literals:
        errors.append("query contains unsafe semicolon outside Logan string literal")
    stripped = _strip_string_literals(query)
    for pattern in LOGAN_UNSUPPORTED_PATTERNS:
        if pattern.search(stripped):
            errors.append(f"unsupported Logan output token: {pattern.pattern}")
    for stats_match in re.finditer(r"\|\s*stats\b(?P<body>[^|]*?)\bby\b(?P<fields>[^|]+)", stripped, flags=re.IGNORECASE):
        by_fields = [field.strip() for field in _split_top_level(stats_match.group("fields"))]
        if "Time" in by_fields:
            errors.append("unsupported OCI time grouping: Time")
    if re.search(r"(?<!https):\s*[A-Za-z_][A-Za-z0-9_]*", stripped):
        errors.append("query contains colon placeholder syntax")
    allowed_fields = mapping.get("allowed_fields", set())
    aliases = _extract_query_aliases(query)
    for field in sorted(_extract_query_field_references(query)):
        if field not in allowed_fields and field not in aliases:
            errors.append(f"unsupported OCI field reference: {field}")
    for field in sorted(_extract_unquoted_operator_fields(query)):
        if field not in allowed_fields and field not in aliases:
            errors.append(f"unsupported OCI field reference: {field}")
    return sorted(set(errors))
