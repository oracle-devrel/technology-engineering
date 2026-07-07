"""KQL source-table extraction and Logan ``Log Source`` filter resolution.

Extracted verbatim from ``scripts/kql/_facade_impl.py`` (plan T5).
"""

from __future__ import annotations

import re
from typing import Iterable

from scripts.kql._constants import SearchStage
from scripts.kql._fields import _escape_logan_string
from scripts.kql._text_utils import (
    _preprocess_simple_lets,
    _split_kql_stages,
    _split_top_level,
    _strip_kql_comments,
    _strip_set_directives,
)


def _clean_table_name(raw: str) -> str:
    text = raw.strip()
    text = re.sub(r"^\s*\(", "", text)
    text = re.sub(r"\)\s*$", "", text)
    text = text.split()[0] if text.split() else text
    text = re.sub(r"\(.*$", "", text)
    return text.strip("`'\" ,")


def _strip_table_extraction_preamble(kql: str) -> str:
    """Remove KQL constructs that precede the source stage but are not sources."""

    text = _strip_set_directives(_strip_kql_comments(kql)).strip()
    preprocessed, errors = _preprocess_simple_lets(text)
    if not errors:
        text = preprocessed.strip()

    while True:
        match = re.match(
            r"\s*declare\s+query_parameters\s*\([\s\S]*?\)\s*;\s*",
            text,
            flags=re.IGNORECASE,
        )
        if not match:
            break
        text = text[match.end():].strip()
    return text


def _take_parenthesized_prefix(text: str) -> tuple[str, str]:
    """Return the first parenthesized clause and trailing text."""
    if not text.startswith("("):
        return "", text
    quote: str | None = None
    depth = 0
    for index, char in enumerate(text):
        if quote:
            if char == quote:
                quote = None
            continue
        if char in ("'", '"'):
            quote = char
            continue
        if char == "(":
            depth += 1
            continue
        if char == ")":
            depth -= 1
            if depth == 0:
                return text[1:index], text[index + 1:].strip()
    return "", text


def _strip_search_options(body: str) -> str:
    """Remove supported search options that do not affect Logan output."""
    text = body.strip()
    while True:
        match = re.match(
            r"(?:kind|withsource)\s*=\s*[A-Za-z_][A-Za-z0-9_]*\s+",
            text,
            flags=re.IGNORECASE,
        )
        if not match:
            return text
        text = text[match.end():].lstrip()


def _parse_search_stage(stage: str) -> SearchStage | None:
    """Parse KQL ``search`` stages, including ``search in (...)``."""
    if not re.match(r"\s*search\b", stage, flags=re.IGNORECASE):
        return None

    body = re.sub(r"^\s*search\b", "", stage, flags=re.IGNORECASE).strip()
    body = _strip_search_options(body)
    tables: list[str] = []
    expression = body
    if re.match(r"in\b", body, flags=re.IGNORECASE):
        remainder = re.sub(r"^in\b", "", body, flags=re.IGNORECASE).strip()
        table_clause, expression = _take_parenthesized_prefix(remainder)
        if table_clause:
            tables = [_clean_table_name(part) for part in _split_top_level(table_clause) if _clean_table_name(part)]
        else:
            parts = remainder.split(maxsplit=1)
            if parts:
                tables = [_clean_table_name(parts[0])]
                expression = parts[1].strip() if len(parts) > 1 else ""
    return SearchStage(tables=tables, expression=expression.strip())


def _extract_union_tables(source: str) -> list[str]:
    union_body = source[6:].strip()
    union_body = re.sub(
        r"\b(?:isfuzzy|kind|withsource)\s*=\s*[^,\s(]+",
        "",
        union_body,
        flags=re.IGNORECASE,
    ).strip()
    tables: list[str] = []
    for part in _split_union_operands(union_body):
        table = _clean_table_name(part)
        if table and table.lower() not in {"union"} and "=" not in part.split("|", 1)[0] and table not in tables:
            tables.append(table)
    return tables


def _split_union_operands(union_body: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    quote: str | None = None
    depth = 0
    for char in union_body:
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
        if char == "," and depth == 0:
            candidate = "".join(current).strip()
            if candidate.startswith("(") or "|" not in candidate:
                if candidate:
                    parts.append(candidate)
                current = []
                continue
        current.append(char)
    tail = "".join(current).strip()
    if tail:
        parts.append(tail)
    return parts


def extract_source_tables(kql: str) -> list[str]:
    """Extract simple KQL source table names from the first stage."""
    kql = _strip_table_extraction_preamble(kql)
    stages = _split_kql_stages(kql)
    if not stages:
        return []
    source = stages[0].strip()
    if re.match(r"^(?:declare|let)\b", source, flags=re.IGNORECASE):
        return []
    if re.match(r"^find\b", source, flags=re.IGNORECASE):
        return []
    source = re.sub(r"^\(\s*union\b", "union", source, flags=re.IGNORECASE)
    search_stage = _parse_search_stage(source)
    if search_stage:
        return search_stage.tables
    if source.lower().startswith("union "):
        return _extract_union_tables(source)
    return [_clean_table_name(source)] if _clean_table_name(source) else []


def _source_filter_for_tables(tables: Iterable[str], mapping: dict) -> tuple[str, list[str], str, str]:
    table_config = mapping["tables"]
    sources: list[str] = []
    categories: list[str] = []
    services: list[str] = []
    for table in tables:
        config = table_config.get(table)
        if not config:
            continue
        for source in config.get("sources", []):
            if source not in sources:
                sources.append(source)
        category = config.get("category", "unknown")
        service = config.get("service", category)
        if category not in categories:
            categories.append(category)
        if service not in services:
            services.append(service)

    if not sources:
        return "", [], "", ""
    filters = [f"'Log Source' = '{_escape_logan_string(source)}'" for source in sources]
    if len(filters) == 1:
        return filters[0], sources, categories[0], services[0]
    return "(" + " or ".join(filters) + ")", sources, categories[0], services[0]
