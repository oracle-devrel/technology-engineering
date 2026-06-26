"""KQL pipeline-operator conversions (project/extend/summarize/sort/top, the
scalar-expression lowering, and the field-clause / alias helpers they share).

Extracted verbatim from ``scripts/kql/_facade_impl.py`` (plan T5).
"""

from __future__ import annotations

import re

from scripts.kql._constants import (
    ENTITY_ENRICHMENT_ALIASES_NORMALIZED,
    SCALAR_CAST_FUNCTIONS,
    SUPPORTED_AGGREGATIONS,
)
from scripts.kql._fields import (
    _format_value,
    _literal_value,
    _normalize_field_name,
    _record_field_error,
    map_field,
)
from scripts.kql._predicates import convert_predicate
from scripts.kql._text_utils import _split_top_level


def _convert_fields_clause(
    clause: str,
    mapping: dict,
    errors: list[str] | None = None,
    allowed_aliases: set[str] | None = None,
) -> str:
    fields = []
    for field in _split_top_level(clause):
        alias, expression = _split_alias_expression(field)
        column_ifexists = _column_ifexists_field(expression)
        if column_ifexists:
            fields.append(map_field(column_ifexists, mapping, errors, allowed_aliases))
            continue
        bin_match = re.fullmatch(
            r"bin\s*\(\s*(?P<field>[A-Za-z_][A-Za-z0-9_]*)\s*,\s*[^)]+\)",
            expression.strip(),
            flags=re.IGNORECASE,
        )
        if bin_match and bin_match.group("field") in {"TimeGenerated", "Timestamp"}:
            fields.append("Time")
            continue
        if alias and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", expression):
            fields.append(map_field(expression, mapping, errors, allowed_aliases))
            continue
        if alias:
            _record_field_error(errors, f"unsupported project expression: {field}")
            continue
        fields.append(map_field(field, mapping, errors, allowed_aliases))
    return ", ".join(fields)


def _column_ifexists_field(expression: str) -> str:
    match = re.fullmatch(
        r"column_ifexists\s*\(\s*(?P<field>'[^']+'|\"[^\"]+\"|[A-Za-z_][A-Za-z0-9_]*)\s*,\s*(?P<fallback>[^)]*)\)",
        expression.strip(),
        flags=re.IGNORECASE,
    )
    if not match:
        return ""
    return _literal_value(match.group("field"))


def _span_to_logan(span: str) -> str:
    match = re.fullmatch(r"\s*(?P<count>\d+)\s*(?P<unit>ms|s|m|h|d)\s*", span, flags=re.IGNORECASE)
    if not match:
        return span.strip()
    unit = match.group("unit").lower()
    unit_map = {
        "ms": "millisecond",
        "s": "second",
        "m": "minute",
        "h": "hour",
        "d": "day",
    }
    return f"{match.group('count')}{unit_map[unit]}"


def _split_time_bin(by_clause: str) -> tuple[str, str]:
    fields = []
    span = ""
    for field in _split_top_level(by_clause):
        match = re.fullmatch(
            r"bin\s*\(\s*(?P<field>TimeGenerated|Timestamp)\s*,\s*(?P<span>[^)]+)\)",
            field.strip(),
            flags=re.IGNORECASE,
        )
        if match:
            span = _span_to_logan(match.group("span"))
        else:
            fields.append(field)
    return span, ", ".join(fields)


def _sanitize_alias(alias: str, fallback: str) -> str:
    raw = alias.strip().strip("'\"")
    if not raw:
        raw = fallback
    raw = re.sub(r"[^A-Za-z0-9_]+", "_", raw).strip("_")
    if not raw:
        raw = fallback
    if raw[0].isdigit():
        raw = f"m_{raw}"
    return raw


def _default_aggregate_alias(func: str, field: str, index: int) -> str:
    if func == "count":
        return "count_"
    if _normalize_field_name(field) in {"TimeGenerated", "Timestamp"}:
        field = "Time"
    field_alias = _sanitize_alias(field, f"{func}_{index}")
    if func in {"make_set", "makeset"}:
        return f"set_{field_alias}"
    if func in {"make_list", "makelist"}:
        return f"list_{field_alias}"
    if func in {"take_any", "any"}:
        return f"any_{field_alias}"
    return f"{func}_{index}"


def _unique_alias(alias: str, used_aliases: set[str]) -> str:
    """Return a deterministic alias that does not collide with previous aliases."""
    if alias not in used_aliases:
        used_aliases.add(alias)
        return alias
    suffix = 2
    while f"{alias}_{suffix}" in used_aliases:
        suffix += 1
    unique = f"{alias}_{suffix}"
    used_aliases.add(unique)
    return unique


def _split_alias_expression(raw: str) -> tuple[str, str]:
    depth = 0
    quote: str | None = None
    for index, char in enumerate(raw):
        if quote:
            if char == quote:
                quote = None
            continue
        if char in ("'", '"'):
            quote = char
            continue
        if char in "([{":
            depth += 1
        elif char in ")]}" and depth:
            depth -= 1
        elif char == "=" and depth == 0:
            return raw[:index].strip(), raw[index + 1:].strip()
    return "", raw.strip()


def _summarize_by_only_clause(clause: str) -> str:
    return re.sub(r"^\s*by\s+", "", clause, flags=re.IGNORECASE).strip()


def _convert_summarize(
    stage: str,
    mapping: dict,
    allowed_aliases: set[str] | None = None,
) -> tuple[str, list[str], set[str]]:
    clause = re.sub(r"^\s*summarize\s+", "", stage, flags=re.IGNORECASE).strip()
    by_only_clause = _summarize_by_only_clause(clause)
    if by_only_clause != clause:
        errors: list[str] = []
        fields_clause = _convert_fields_clause(by_only_clause, mapping, errors, allowed_aliases)
        return f"stats count as Count by {fields_clause}", errors, {"Count"}

    parts = re.split(r"\s+by\s+", clause, maxsplit=1, flags=re.IGNORECASE)
    aggregate_clause = parts[0].strip()
    by_clause = parts[1].strip() if len(parts) == 2 else ""
    time_span, non_time_by_clause = _split_time_bin(by_clause) if by_clause else ("", "")
    errors = []
    aggregates = []
    aggregate_aliases: set[str] = set()
    used_aliases = set(allowed_aliases or set())
    for index, raw_aggregate in enumerate(_split_top_level(aggregate_clause), start=1):
        alias, expression = _split_alias_expression(raw_aggregate)
        match = re.fullmatch(r"(?P<func>[A-Za-z_][A-Za-z0-9_]*)\s*\((?P<field>[^)]*)\)", expression.strip())
        if not match:
            errors.append(f"unsupported summarize aggregate: {raw_aggregate}")
            continue
        func = match.group("func").lower()
        if func not in SUPPORTED_AGGREGATIONS and func != "countif":
            errors.append(f"unsupported summarize aggregate: {raw_aggregate}")
            continue
        field = match.group("field").strip()
        field_args = _split_top_level(field)
        field = field_args[0].strip() if field_args else field
        alias = _sanitize_alias(alias, f"{func}_{index}") if alias else _default_aggregate_alias(func, field, index)
        alias = _unique_alias(alias, used_aliases)
        aggregate_aliases.add(alias)
        if func == "countif":
            predicate, predicate_errors = convert_predicate(field, mapping, allowed_aliases)
            errors.extend(predicate_errors)
            if predicate:
                aggregates.append(f"sum(if({predicate}, 1, 0)) as {alias}")
            continue

        mapped_func = SUPPORTED_AGGREGATIONS[func]
        if func == "count" and not field:
            aggregates.append(f"count as {alias}")
        else:
            aggregates.append(f"{mapped_func}({map_field(field, mapping, errors, allowed_aliases)}) as {alias}")

    if not aggregates:
        errors.append("summarize stage did not produce supported aggregates")
        return "", errors, aggregate_aliases

    if time_span:
        command = f"timestats span = {time_span} {', '.join(aggregates)}"
        if non_time_by_clause:
            command = f"{command} by {_convert_fields_clause(non_time_by_clause, mapping, errors, allowed_aliases)}"
        return command, errors, aggregate_aliases
    if by_clause:
        return (
            f"stats {', '.join(aggregates)} by {_convert_fields_clause(by_clause, mapping, errors, allowed_aliases)}",
            errors,
            aggregate_aliases,
        )
    return f"stats {', '.join(aggregates)}", errors, aggregate_aliases


def _convert_sort(stage: str, mapping: dict, errors: list[str], allowed_aliases: set[str]) -> str:
    clause = re.sub(r"^\s*(?:sort|order)\s+(?:by\s+)?", "", stage, flags=re.IGNORECASE).strip()
    first = _split_top_level(clause)[0] if _split_top_level(clause) else clause
    tokens = first.split()
    field = tokens[0] if tokens else first
    direction = tokens[1].lower() if len(tokens) > 1 else "desc"
    mapped = map_field(field, mapping, errors, allowed_aliases)
    prefix = "-" if direction in {"desc", "descending"} else ""
    return f"sort {prefix}{mapped}"


def _convert_top(stage: str, mapping: dict, errors: list[str], allowed_aliases: set[str]) -> list[str]:
    match = re.match(r"top\s+(?P<count>\d+)(?:\s+by\s+(?P<field>[A-Za-z_][A-Za-z0-9_']*)(?:\s+(?P<direction>asc|desc))?)?", stage, flags=re.IGNORECASE)
    if not match:
        return []
    commands = []
    field = match.group("field")
    if field:
        direction = match.group("direction") or "desc"
        mapped = map_field(field, mapping, errors, allowed_aliases)
        commands.append(f"sort {'-' if direction.lower() == 'desc' else ''}{mapped}")
    commands.append(f"head {match.group('count')}")
    return commands


def _find_top_level_binary(expression: str) -> tuple[str, str, str] | None:
    quote: str | None = None
    depth = 0
    for index in range(len(expression) - 1, -1, -1):
        char = expression[index]
        if quote:
            if char == quote:
                quote = None
            continue
        if char in ("'", '"'):
            quote = char
            continue
        if char in ")]}":
            depth += 1
            continue
        if char in "([{":
            if depth:
                depth -= 1
            continue
        if depth == 0 and char in {"+", "-", "*", "/"}:
            left = expression[:index].strip()
            right = expression[index + 1:].strip()
            if left and right:
                return left, char, right
    return None


def _function_args(expression: str, function_name: str) -> list[str] | None:
    pattern = rf"{re.escape(function_name)}\s*\((?P<body>.*)\)"
    match = re.fullmatch(pattern, expression.strip(), flags=re.IGNORECASE)
    if not match:
        return None
    return _split_top_level(match.group("body"))


def _convert_scalar_expression(
    expression: str,
    mapping: dict,
    errors: list[str],
    allowed_aliases: set[str],
) -> str:
    expr = expression.strip()
    if not expr:
        errors.append("unsupported empty scalar expression")
        return "''"

    column_field = _column_ifexists_field(expr)
    if column_field:
        return map_field(column_field, mapping, errors, allowed_aliases)

    iff_args = _function_args(expr, "iff") or _function_args(expr, "iif")
    if iff_args is not None:
        if len(iff_args) != 3:
            errors.append("unsupported scalar function: iff")
            return "''"
        predicate, predicate_errors = convert_predicate(iff_args[0], mapping, allowed_aliases)
        errors.extend(predicate_errors)
        true_value = _convert_scalar_expression(iff_args[1], mapping, errors, allowed_aliases)
        false_value = _convert_scalar_expression(iff_args[2], mapping, errors, allowed_aliases)
        return f"if({predicate}, {true_value}, {false_value})" if predicate else true_value

    case_args = _function_args(expr, "case")
    if case_args is not None:
        if len(case_args) < 3 or len(case_args) % 2 == 0:
            errors.append("unsupported scalar function: case")
            return "''"
        fallback = _convert_scalar_expression(case_args[-1], mapping, errors, allowed_aliases)
        for predicate_expression, value_expression in reversed(list(zip(case_args[0:-1:2], case_args[1:-1:2]))):
            predicate, predicate_errors = convert_predicate(predicate_expression, mapping, allowed_aliases)
            errors.extend(predicate_errors)
            value = _convert_scalar_expression(value_expression, mapping, errors, allowed_aliases)
            fallback = f"if({predicate}, {value}, {fallback})" if predicate else value
        return fallback

    # KQL type-cast wrappers are no-ops in Logan QL's dynamically typed
    # ``eval`` context: ``toint(x)``/``todouble(x)``/``tobool(x)`` all compare
    # and render identically to ``x``. Unwrap them to the inner expression so
    # the cast wrapper never blocks an otherwise-supported conversion.
    for cast_name in SCALAR_CAST_FUNCTIONS:
        args = _function_args(expr, cast_name)
        if args is not None:
            if len(args) != 1:
                errors.append(f"unsupported scalar function: {cast_name}")
                return "''"
            return _convert_scalar_expression(args[0], mapping, errors, allowed_aliases)

    for function_name, logan_name in (("tolower", "lower"), ("toupper", "upper")):
        args = _function_args(expr, function_name)
        if args is not None:
            if len(args) != 1:
                errors.append(f"unsupported scalar function: {function_name}")
                return "''"
            return f"{logan_name}({_convert_scalar_expression(args[0], mapping, errors, allowed_aliases)})"

    # ``materialize(x)`` is a query-caching hint with no Logan equivalent;
    # the cached subexpression is semantically equal to ``x``, so unwrap it.
    materialize_args = _function_args(expr, "materialize")
    if materialize_args is not None:
        if len(materialize_args) != 1:
            errors.append("unsupported scalar function: materialize")
            return "''"
        return _convert_scalar_expression(materialize_args[0], mapping, errors, allowed_aliases)

    # ``strlen(x)`` -> Logan ``length(x)``.
    strlen_args = _function_args(expr, "strlen")
    if strlen_args is not None:
        if len(strlen_args) != 1:
            errors.append("unsupported scalar function: strlen")
            return "''"
        return f"length({_convert_scalar_expression(strlen_args[0], mapping, errors, allowed_aliases)})"

    # ``strcat_delim(delim, a, b, ...)`` -> Logan ``concat(a, delim, b, ...)``.
    # The KQL delimiter is interleaved between the value arguments; Logan has no
    # delimiter-aware concat so we splice the (converted) delimiter literal in
    # between each value, reusing the proven ``concat`` lowering.
    strcat_delim_args = _function_args(expr, "strcat_delim")
    if strcat_delim_args is not None:
        if len(strcat_delim_args) < 3:
            errors.append("unsupported scalar function: strcat_delim")
            return "''"
        delimiter = _convert_scalar_expression(
            strcat_delim_args[0], mapping, errors, allowed_aliases
        )
        values = [
            _convert_scalar_expression(arg, mapping, errors, allowed_aliases)
            for arg in strcat_delim_args[1:]
        ]
        interleaved: list[str] = []
        for index, value in enumerate(values):
            if index:
                interleaved.append(delimiter)
            interleaved.append(value)
        return f"concat({', '.join(interleaved)})"

    # ``strcat(a, b, ...)`` -> Logan ``concat(a, b, ...)``.
    strcat_args = _function_args(expr, "strcat")
    if strcat_args is not None:
        if len(strcat_args) < 2:
            errors.append("unsupported scalar function: strcat")
            return "''"
        converted = [
            _convert_scalar_expression(arg, mapping, errors, allowed_aliases)
            for arg in strcat_args
        ]
        return f"concat({', '.join(converted)})"

    # KQL ``extract(regex, captureGroup, source)`` -> Logan
    # ``extract(source, /regex/)``. Logan addresses the first capture group of
    # the supplied regex; capture-group indices other than 1 cannot be
    # expressed and are SKIPPED to avoid silently changing semantics.
    extract_args = _function_args(expr, "extract")
    if extract_args is not None:
        if len(extract_args) != 3:
            errors.append(f"unsupported scalar function: extract({len(extract_args)} args)")
            return "''"
        regex_arg, group_arg, source_arg = extract_args
        group_text = group_arg.strip()
        if group_text not in {"1"}:
            errors.append(f"unsupported extract capture group: {group_text}")
            return "''"
        regex_literal = _literal_value(regex_arg.strip())
        if "/" in regex_literal:
            errors.append("unsupported extract regex: contains slash delimiter")
            return "''"
        source = _convert_scalar_expression(source_arg, mapping, errors, allowed_aliases)
        return f"extract({source}, /{regex_literal}/)"

    binary = _find_top_level_binary(expr)
    if binary is not None:
        left, operator, right = binary
        left_value = _convert_scalar_expression(left, mapping, errors, allowed_aliases)
        right_value = _convert_scalar_expression(right, mapping, errors, allowed_aliases)
        return f"{left_value} {operator} {right_value}"

    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", expr):
        return map_field(expr, mapping, errors, allowed_aliases)
    if re.fullmatch(r"-?\d+(?:\.\d+)?", expr):
        return expr
    if expr.lower() in {"true", "false", "null"}:
        return _format_value(expr)
    if (expr.startswith("'") and expr.endswith("'")) or (expr.startswith('"') and expr.endswith('"')):
        return _format_value(expr)

    errors.append(f"unsupported scalar expression: {expression}")
    return _format_value(expr)


def _convert_extend(stage: str, mapping: dict, allowed_aliases: set[str]) -> tuple[list[str], list[str], set[str]]:
    clause = re.sub(r"^\s*extend\s+", "", stage, flags=re.IGNORECASE).strip()
    commands = []
    errors = []
    aliases: set[str] = set()
    for assignment in _split_top_level(clause):
        alias, expression = _split_alias_expression(assignment)
        if not alias:
            errors.append(f"unsupported extend expression: {assignment}")
            continue
        sanitized_alias = _sanitize_alias(alias, "extended_field")
        if sanitized_alias.lower() in ENTITY_ENRICHMENT_ALIASES_NORMALIZED:
            continue
        iff_args = _function_args(expression, "iff") or _function_args(expression, "iif")
        if iff_args is not None:
            if len(iff_args) != 3:
                errors.append(f"unsupported extend expression: {assignment}")
                continue
            predicate, predicate_errors = convert_predicate(iff_args[0], mapping, allowed_aliases)
            errors.extend(predicate_errors)
            true_value = _convert_scalar_expression(iff_args[1], mapping, errors, allowed_aliases)
            false_value = _convert_scalar_expression(iff_args[2], mapping, errors, allowed_aliases)
            rhs = f"if({predicate}, {true_value}, {false_value})" if predicate else true_value
        else:
            rhs = _convert_scalar_expression(expression, mapping, errors, allowed_aliases)
        aliases.add(sanitized_alias)
        commands.append(f"eval {sanitized_alias} = {rhs}")
    return commands, errors, aliases


def _convert_project(stage: str, mapping: dict, allowed_aliases: set[str]) -> tuple[list[str], list[str], set[str]]:
    clause = re.sub(r"^\s*project(?:-reorder)?\s+", "", stage, flags=re.IGNORECASE).strip()
    commands: list[str] = []
    errors: list[str] = []
    aliases: set[str] = set()
    fields: list[str] = []
    current_aliases = set(allowed_aliases)
    for item in _split_top_level(clause):
        alias, expression = _split_alias_expression(item)
        if alias:
            sanitized_alias = _sanitize_alias(alias, "project_field")
            rhs = _convert_scalar_expression(expression, mapping, errors, current_aliases)
            aliases.add(sanitized_alias)
            current_aliases.add(sanitized_alias)
            commands.append(f"eval {sanitized_alias} = {rhs}")
            fields.append(sanitized_alias)
            continue
        fields_clause = _convert_fields_clause(item, mapping, errors, current_aliases)
        if fields_clause:
            fields.append(fields_clause)
    if fields:
        commands.append(f"fields {', '.join(fields)}")
    return commands, sorted(set(errors)), aliases
