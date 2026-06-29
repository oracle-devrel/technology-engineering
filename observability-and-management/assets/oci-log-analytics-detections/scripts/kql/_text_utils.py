"""Lexical helpers for the KQL→Logan converter: literal/comment stripping,
top-level splitting, ``let`` preprocessing, and unsupported-construct
classification.

Extracted verbatim from ``scripts/kql/_facade_impl.py`` (plan T5). Depends
only on the pattern tables in ``_constants``.
"""

from __future__ import annotations

import re

from scripts.kql._constants import UNSUPPORTED_PATTERNS


def _strip_string_literals(text: str) -> str:
    """Replace quoted strings with empty quotes for safe token scanning."""
    return re.sub(r"'(?:\\'|[^'])*'|\"(?:\\\"|[^\"])*\"", "''", text)


def _strip_single_quoted_literals(text: str) -> str:
    """Remove Logan single-quoted literals while preserving unsafe outside tokens."""
    stripped: list[str] = []
    in_quote = False
    escaped = False
    for char in text:
        if in_quote:
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if char == "'":
                in_quote = False
                stripped.append("''")
            continue
        if char == "'":
            in_quote = True
            escaped = False
            continue
        stripped.append(char)
    return "".join(stripped)


def _strip_kql_comments(kql: str) -> str:
    lines = []
    for line in kql.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("//") or stripped.startswith("#"):
            continue
        quote: str | None = None
        escaped = False
        cleaned: list[str] = []
        index = 0
        while index < len(line):
            char = line[index]
            if escaped:
                cleaned.append(char)
                escaped = False
                index += 1
                continue
            if quote:
                cleaned.append(char)
                if char == "\\":
                    escaped = True
                elif char == quote:
                    quote = None
                index += 1
                continue
            if char in ("'", '"'):
                quote = char
                cleaned.append(char)
                index += 1
                continue
            if char == "/" and index + 1 < len(line) and line[index + 1] == "/":
                break
            cleaned.append(char)
            index += 1
        cleaned_line = "".join(cleaned).rstrip()
        if cleaned_line.strip():
            lines.append(cleaned_line)
    return "\n".join(lines).strip()


def _find_top_level_semicolon(text: str) -> int:
    quote: str | None = None
    escaped = False
    depth = 0
    for index, char in enumerate(text):
        if escaped:
            escaped = False
            continue
        if quote:
            if char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in ("'", '"'):
            quote = char
            continue
        if char in "([{":
            depth += 1
        elif char in ")]}" and depth:
            depth -= 1
        elif char == ";" and depth == 0:
            return index
    return -1


def _normalize_simple_let_expression(expression: str) -> str | None:
    value = expression.strip()
    if not value:
        return None
    stripped = _strip_string_literals(value)
    if "|" in stripped or ";" in stripped:
        return None
    if re.search(
        r"\b(?:datatable|externaldata|join|materialize|project|summarize|table|toscalar|union|where)\b",
        stripped,
        re.IGNORECASE,
    ):
        return None

    array_match = re.fullmatch(
        r"(?:dynamic|pack_array)\s*\(\s*\[(?P<values>[\s\S]*)\]\s*\)",
        value,
        flags=re.IGNORECASE,
    )
    if array_match:
        values = array_match.group("values").strip()
        return values or None

    if value.startswith("[") and value.endswith("]"):
        values = value[1:-1].strip()
        return values or None

    if re.fullmatch(r"-?\d+(?:\.\d+)?", value):
        return value
    if re.fullmatch(r"\d+(?:\.\d+)?(?:d|h|m|s|ms)", value, flags=re.IGNORECASE):
        return value
    if value.lower() in {"true", "false"}:
        return value.lower()
    if re.fullmatch(r"(?:ago|datetime)\s*\([^|;]+\)", value, flags=re.IGNORECASE):
        return value
    if re.fullmatch(r"now\s*\(\s*\)", value, flags=re.IGNORECASE):
        return value
    if re.fullmatch(r"@?(?:'[^']*'|\"[^\"]*\")", value, flags=re.DOTALL):
        return value
    return None


def _replace_unquoted_variables(text: str, variables: dict[str, str]) -> str:
    if not variables:
        return text
    names = set(variables)
    output: list[str] = []
    quote: str | None = None
    escaped = False
    index = 0
    while index < len(text):
        char = text[index]
        if escaped:
            output.append(char)
            escaped = False
            index += 1
            continue
        if quote:
            output.append(char)
            if char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            index += 1
            continue
        if char in ("'", '"'):
            quote = char
            output.append(char)
            index += 1
            continue
        if char.isalpha() or char == "_":
            end = index + 1
            while end < len(text) and (text[end].isalnum() or text[end] == "_"):
                end += 1
            token = text[index:end]
            output.append(variables[token] if token in names else token)
            index = end
            continue
        output.append(char)
        index += 1
    return "".join(output)


def _strip_set_directives(kql: str) -> str:
    """Remove supported Sentinel query directives before conversion."""

    text = kql.strip()
    supported = r"(?:timeout|truncationmaxsize|query_take_max_records)"
    while True:
        match = re.match(
            rf"\s*set\s+{supported}\s*=\s*[^;\n]+(?:;|\n)",
            text,
            flags=re.IGNORECASE,
        )
        if not match:
            break
        text = text[match.end():].lstrip()
    return text


def _preprocess_simple_lets(kql: str) -> tuple[str, list[str]]:
    text = _strip_set_directives(_strip_kql_comments(kql)).strip()
    variables: dict[str, str] = {}
    while True:
        match = re.match(r"\s*let\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=", text, flags=re.IGNORECASE)
        if not match:
            break
        remainder = text[match.end():]
        semicolon = _find_top_level_semicolon(remainder)
        if semicolon < 0:
            return text, ["unsupported KQL construct: let variables"]
        expression = remainder[:semicolon].strip()
        normalized = _normalize_simple_let_expression(expression)
        if normalized is None:
            return text, ["unsupported KQL construct: let variables"]
        variables[match.group("name")] = normalized
        text = remainder[semicolon + 1:].lstrip()

    if re.search(r"\blet\s+\w+\s*=", _strip_string_literals(text), flags=re.IGNORECASE):
        return text, ["unsupported KQL construct: let variables"]
    return _replace_unquoted_variables(text, variables), []


def _split_top_level(text: str, delimiter: str = ",") -> list[str]:
    parts = []
    current = []
    quote: str | None = None
    depth = 0
    for char in text:
        if quote:
            current.append(char)
            if char == quote:
                quote = None
            continue
        if char in ("'", '"'):
            quote = char
            current.append(char)
            continue
        if char in "([{":
            depth += 1
        elif char in ")]}" and depth:
            depth -= 1
        if char == delimiter and depth == 0:
            part = "".join(current).strip()
            if part:
                parts.append(part)
            current = []
            continue
        current.append(char)
    part = "".join(current).strip()
    if part:
        parts.append(part)
    return parts


def _split_kql_stages(kql: str) -> list[str]:
    stages = []
    current = []
    quote: str | None = None
    depth = 0
    for char in _strip_kql_comments(kql):
        if quote:
            current.append(char)
            if char == quote:
                quote = None
            continue
        if char in ("'", '"'):
            quote = char
            current.append(char)
            continue
        if char in "([{":
            depth += 1
        elif char in ")]}" and depth:
            depth -= 1
        if char == "|" and depth == 0:
            part = "".join(current).strip()
            if part:
                stages.append(part)
            current = []
            continue
        current.append(char)
    part = "".join(current).strip()
    if part:
        stages.append(part)
    return stages


def _classify_unsupported_kql_text(kql: str) -> list[str]:
    """Return deterministic skip reasons for unsupported KQL features."""
    stripped = _strip_string_literals(_strip_set_directives(kql))
    reasons = []
    for pattern, reason in UNSUPPORTED_PATTERNS:
        if pattern.search(stripped):
            reasons.append(reason)
    return sorted(set(reasons))


def classify_unsupported_kql(kql: str) -> list[str]:
    """Return deterministic skip reasons for unsupported KQL features."""
    preprocessed, preprocessing_errors = _preprocess_simple_lets(kql)
    return sorted(set(preprocessing_errors + _classify_unsupported_kql_text(preprocessed)))
