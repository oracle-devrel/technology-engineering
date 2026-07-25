"""KQL predicate and ``search``-expression conversion to Logan QL.

Extracted verbatim from ``scripts/kql/_facade_impl.py`` (plan T5).
"""

from __future__ import annotations

import re

from scripts.kql._constants import SCALAR_CAST_FUNCTIONS
from scripts.kql._fields import (
    _cleanup_boolean_expression,
    _escape_logan_string,
    _field_role,
    _format_value,
    _format_value_for_field,
    _literal_value,
    _normalize_field_name,
    _remove_time_filters,
    map_field,
)
from scripts.kql._text_utils import (
    _split_top_level,
    _strip_kql_comments,
    _strip_string_literals,
)


def convert_predicate(
    predicate: str,
    mapping: dict,
    allowed_aliases: set[str] | None = None,
) -> tuple[str, list[str]]:
    """Convert a supported KQL predicate into Logan QL."""
    expression = _remove_time_filters(_strip_kql_comments(predicate))
    if not expression:
        return "", []

    errors: list[str] = []
    field_token = r"(?:[A-Za-z_][A-Za-z0-9_]*|`[^`]+`|'[^']+'|\"[^\"]+\")"
    identifier_field_token = r"(?:[A-Za-z_][A-Za-z0-9_]*|`[^`]+`)"
    value_token = r"(?:@?'[^']*'|@?\"[^\"]*\"|-?\d+(?:\.\d+)?|true|false|null)"

    def replace_column_ifexists(match: re.Match) -> str:
        return _literal_value(match.group("field"))

    expression = re.sub(
        r"column_ifexists\s*\(\s*(?P<field>'[^']+'|\"[^\"]+\"|[A-Za-z_][A-Za-z0-9_]*)\s*,\s*[^)]*\)",
        replace_column_ifexists,
        expression,
        flags=re.IGNORECASE,
    )

    # Unwrap KQL type-cast wrappers around a single (non-nested) argument so a
    # predicate like ``toint(StatusCode) > 400`` reduces to the supported
    # ``StatusCode > 400`` comparison. The cast is a no-op in Logan QL.
    _cast_unwrap_pattern = (
        r"\b(?:" + "|".join(SCALAR_CAST_FUNCTIONS) + r")\s*\(\s*([^()]+?)\s*\)"
    )
    expression = re.sub(
        _cast_unwrap_pattern,
        lambda match: match.group(1),
        expression,
        flags=re.IGNORECASE,
    )

    def replace_isnotnull(match: re.Match) -> str:
        field = map_field(match.group("field"), mapping, errors, allowed_aliases)
        return f"{field} != null"

    def replace_isnull(match: re.Match) -> str:
        field = map_field(match.group("field"), mapping, errors, allowed_aliases)
        return f"{field} = null"

    expression = re.sub(
        rf"\bisnotnull\s*\(\s*(?P<field>{field_token})\s*\)",
        replace_isnotnull,
        expression,
        flags=re.IGNORECASE,
    )
    expression = re.sub(
        rf"\bisnull\s*\(\s*(?P<field>{field_token})\s*\)",
        replace_isnull,
        expression,
        flags=re.IGNORECASE,
    )

    def replace_between(match: re.Match) -> str:
        field = map_field(match.group("field"), mapping, errors, allowed_aliases)
        low = _format_value_for_field(match.group("low"), field, mapping)
        high = _format_value_for_field(match.group("high"), field, mapping)
        clause = f"({field} >= {low} and {field} <= {high})"
        return f"not {clause}" if match.group("neg") else clause

    expression = re.sub(
        rf"(?P<field>{field_token})\s+(?P<neg>!|not\s+)?between\s*\(\s*(?P<low>[^.()]+?)\s*\.\.\s*(?P<high>[^)]+?)\s*\)",
        replace_between,
        expression,
        flags=re.IGNORECASE,
    )

    def replace_isnotempty(match: re.Match) -> str:
        field = map_field(match.group("field"), mapping, errors, allowed_aliases)
        return f"({field} != null and {field} != '')"

    def replace_isempty(match: re.Match) -> str:
        field = map_field(match.group("field"), mapping, errors, allowed_aliases)
        return f"({field} = null or {field} = '')"

    expression = re.sub(
        rf"\bisnotempty\s*\(\s*(?P<field>{field_token})\s*\)",
        replace_isnotempty,
        expression,
        flags=re.IGNORECASE,
    )
    expression = re.sub(
        rf"\bisempty\s*\(\s*(?P<field>{field_token})\s*\)",
        replace_isempty,
        expression,
        flags=re.IGNORECASE,
    )

    def replace_in(match: re.Match) -> str:
        field = map_field(match.group("field"), mapping, errors, allowed_aliases)
        values = [_format_value_for_field(value, field, mapping) for value in _split_top_level(match.group("values"))]
        operator = "not in" if match.group("op").lower().startswith(("!", "not")) else "in"
        return f"{field} {operator} ({', '.join(values)})"

    expression = re.sub(
        rf"(?P<field>{field_token})\s+(?P<op>in~?|!in~?|not\s+in~?)\s*\((?P<values>[^)]*)\)",
        replace_in,
        expression,
        flags=re.IGNORECASE,
    )

    def replace_collection_string_operator(match: re.Match) -> str:
        field = map_field(match.group("field"), mapping, errors, allowed_aliases)
        op = match.group("op").lower()
        connector = " and " if op == "has_all" else " or "
        clauses = []
        for value in _split_top_level(match.group("values")):
            formatted = _format_value(value)
            raw_value = formatted[1:-1] if formatted.startswith("'") and formatted.endswith("'") else formatted
            clauses.append(f"{field} like '{_escape_logan_string('*' + raw_value + '*')}'")
        clause = connector.join(clauses)
        if len(clauses) > 1:
            clause = f"({clause})"
        return f"not ({clause})" if match.group("neg") else clause

    expression = re.sub(
        rf"(?P<field>{field_token})\s+(?P<neg>!|not\s+)?(?P<op>has_any|has_all)\s*\((?P<values>[^)]*)\)",
        replace_collection_string_operator,
        expression,
        flags=re.IGNORECASE,
    )

    def replace_string_operator(match: re.Match) -> str:
        field = map_field(match.group("field"), mapping, errors, allowed_aliases)
        value = match.group("value").strip()
        if value.startswith("(") and value.endswith(")"):
            value = value[1:-1].strip()
        if value.startswith("@"):
            value = value[1:].strip()
        raw_value = value[1:-1] if value[:1] in {"'", '"'} and value[-1:] == value[:1] else value
        op = match.group("op").lower().replace("_cs", "")
        if op in {"has", "contains"}:
            pattern = f"*{raw_value}*"
        elif op in {"startswith", "hasprefix"}:
            pattern = f"{raw_value}*"
        elif op in {"endswith", "hassuffix"}:
            pattern = f"*{raw_value}"
        else:
            pattern = raw_value
        clause = f"{field} like '{_escape_logan_string(pattern)}'"
        return f"not ({clause})" if match.group("neg") else clause

    expression = re.sub(
        rf"(?P<field>{field_token})\s+(?P<neg>!|not\s+)?(?P<op>has_cs|has|hasprefix|hassuffix|contains_cs|contains|startswith|endswith)\s+(?P<value>(?:\(\s*{value_token}\s*\)|{value_token}))",
        replace_string_operator,
        expression,
        flags=re.IGNORECASE,
    )

    def replace_field_comparison(match: re.Match) -> str:
        left_raw = match.group("left")
        right_raw = match.group("right")
        left_role = _field_role(left_raw, mapping)
        right_role = _field_role(right_raw, mapping)
        left_name = _normalize_field_name(left_raw)
        right_name = _normalize_field_name(right_raw)
        if right_name.lower() in {"true", "false", "null"}:
            return match.group(0)
        if left_role and right_role and left_role != right_role:
            errors.append(f"role_mismatch:{left_name}:{right_name}")
        left = map_field(left_raw, mapping, errors, allowed_aliases)
        right = map_field(right_raw, mapping, errors, allowed_aliases)
        op = match.group("op")
        if op in {"==", "=~"}:
            op = "="
        elif op in {"<>", "!~"}:
            op = "!="
        return f"{left} {op} {right}"

    expression = re.sub(
        rf"(?P<left>{identifier_field_token})\s*(?P<op>==|=~|!~|!=|<>|>=|<=|>|<|=)\s*(?P<right>{identifier_field_token})",
        replace_field_comparison,
        expression,
        flags=re.IGNORECASE,
    )

    def replace_comparison(match: re.Match) -> str:
        field = map_field(match.group("field"), mapping, errors, allowed_aliases)
        op = match.group("op")
        if op in {"==", "=~"}:
            op = "="
        elif op in {"<>", "!~"}:
            op = "!="
        return f"{field} {op} {_format_value_for_field(match.group('value'), field, mapping)}"

    expression = re.sub(
        rf"(?P<field>{field_token})\s*(?P<op>==|=~|!~|!=|<>|>=|<=|>|<|=)\s*(?P<value>{value_token})",
        replace_comparison,
        expression,
        flags=re.IGNORECASE,
    )

    expression = _cleanup_boolean_expression(expression)
    leftovers = _strip_string_literals(expression)
    if re.search(r"\b(?:has|has_any|has_all|hasprefix|hassuffix|contains|startswith|endswith|in~)\b|==|=~|!~", leftovers, flags=re.IGNORECASE):
        errors.append(f"unsupported predicate expression: {predicate}")
    if re.search(r"\b(?!(?:and|in|not|or)\b)[A-Za-z_][A-Za-z0-9_]*\s*\(", leftovers, flags=re.IGNORECASE):
        errors.append(f"unsupported predicate expression: {predicate}")
    return expression, sorted(set(errors))


def _free_text_search_clause(value: str) -> str:
    raw_value = _literal_value(value)
    pattern = _escape_logan_string(f"*{raw_value}*")
    return f"('Original Log Content' like '{pattern}' or msg like '{pattern}')"


def _search_expression_looks_like_predicate(expression: str) -> bool:
    stripped = _strip_string_literals(expression)
    return bool(
        re.search(
            r"\b(?:has|has_any|has_all|hasprefix|hassuffix|contains|startswith|endswith|in~?|not\s+in)\b|"
            r"==|=~|!~|!=|<>|>=|<=|(?<!:)[=<>]",
            stripped,
            flags=re.IGNORECASE,
        )
    )


def _convert_search_expression(
    expression: str,
    mapping: dict,
    allowed_aliases: set[str] | None = None,
) -> tuple[str, list[str]]:
    """Convert a KQL search expression into Logan filters.

    KQL ``search`` is broader than a single field predicate. For free-text
    terms, Logan uses the raw-message fields available across parser contracts.
    When the expression is a normal KQL predicate, reuse the predicate mapper so
    fields such as ``CounterName == "..."`` keep their typed OCI mapping.
    """
    text = expression.strip()
    if not text or text == "*":
        return "", []
    if _search_expression_looks_like_predicate(text):
        return convert_predicate(text, mapping, allowed_aliases)

    errors: list[str] = []
    parts: list[str] = []
    previous_clause = False
    tokens = re.findall(r"\(|\)|\b(?:and|or|not)\b|@?'[^']*'|@?\"[^\"]*\"|[^\s()]+", text, flags=re.IGNORECASE)
    for token in tokens:
        lowered = token.lower()
        if token in {"(", ")"}:
            parts.append(token)
            previous_clause = token == ")"
            continue
        if lowered in {"and", "or", "not"}:
            parts.append(lowered)
            previous_clause = False
            continue
        if token == "*":
            continue

        clause = ""
        fielded = re.fullmatch(
            r"(?P<field>[A-Za-z_][A-Za-z0-9_]*)\s*:\s*(?P<value>@?'[^']*'|@?\"[^\"]*\"|[^\s()]+)",
            token,
        )
        if fielded:
            field = map_field(fielded.group("field"), mapping, errors, allowed_aliases)
            raw_value = _literal_value(fielded.group("value"))
            clause = f"{field} like '{_escape_logan_string(f'*{raw_value}*')}'"
        else:
            clause = _free_text_search_clause(token)

        if previous_clause:
            parts.append("and")
        parts.append(clause)
        previous_clause = True
    return _cleanup_boolean_expression(" ".join(parts)), sorted(set(errors))
