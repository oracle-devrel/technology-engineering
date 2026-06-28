"""Top-level KQL→Logan QL pipeline orchestration (``convert_kql_to_logan``).

Extracted verbatim from ``scripts/kql/_facade_impl.py`` (plan T5). Named with
a leading underscore to avoid colliding with the existing thin ``pipeline.py``
delegation shim in this package.
"""

from __future__ import annotations

import re

from scripts.kql._operators import (
    _convert_extend,
    _convert_fields_clause,
    _convert_project,
    _convert_sort,
    _convert_summarize,
    _convert_top,
)
from scripts.kql._predicates import _convert_search_expression, convert_predicate
from scripts.kql._sources import (
    _parse_search_stage,
    _source_filter_for_tables,
    extract_source_tables,
)
from scripts.kql._text_utils import (
    _classify_unsupported_kql_text,
    _preprocess_simple_lets,
    _split_kql_stages,
)


def convert_kql_to_logan(kql: str, mapping: dict) -> tuple[str, dict, list[str]]:
    """Convert a supported KQL query into Logan QL."""
    kql, preprocessing_errors = _preprocess_simple_lets(kql)
    errors = sorted(set(preprocessing_errors + _classify_unsupported_kql_text(kql)))
    if errors:
        return "", {}, errors

    stages = _split_kql_stages(kql)
    if not stages:
        return "", {}, ["empty KQL query"]

    initial_search_stage = _parse_search_stage(stages[0])
    tables = extract_source_tables(kql)
    if initial_search_stage and not tables:
        return "", {}, ["KQL search operator requires mapped in (...) tables"]
    missing_tables = [table for table in tables if table not in mapping["tables"]]
    if missing_tables:
        return "", {}, [f"unsupported Sentinel table: {table}" for table in missing_tables]

    source_filter, sources, category, service = _source_filter_for_tables(tables, mapping)
    if not source_filter:
        return "", {}, ["query did not resolve to a mapped Logan source"]

    filters = [source_filter]
    commands: list[str] = []
    aliases: set[str] = set()

    if initial_search_stage and initial_search_stage.expression:
        predicate, predicate_errors = _convert_search_expression(initial_search_stage.expression, mapping, aliases)
        errors.extend(predicate_errors)
        if predicate:
            filters.append(f"({predicate})")

    for stage in stages[1:]:
        lowered = stage.lower().strip()
        if re.match(r"(?:where|filter)\b", lowered):
            predicate = re.sub(r"^\s*(?:where|filter)\b", "", stage, flags=re.IGNORECASE).strip()
            predicate, predicate_errors = convert_predicate(predicate, mapping, aliases)
            errors.extend(predicate_errors)
            if predicate:
                if commands:
                    commands.append(f"where {predicate}")
                else:
                    filters.append(f"({predicate})")
        elif re.match(r"project-away\b", lowered):
            continue
        elif re.match(r"project(?:-reorder)?\b", lowered):
            project_commands, project_errors, project_aliases = _convert_project(stage, mapping, aliases)
            commands.extend(project_commands)
            errors.extend(project_errors)
            aliases.update(project_aliases)
        elif re.match(r"extend\b", lowered):
            extend_commands, extend_errors, extend_aliases = _convert_extend(stage, mapping, aliases)
            commands.extend(extend_commands)
            errors.extend(extend_errors)
            aliases.update(extend_aliases)
        elif re.match(r"summarize\b", lowered):
            command, summarize_errors, aggregate_aliases = _convert_summarize(stage, mapping, aliases)
            if command:
                commands.append(command)
            errors.extend(summarize_errors)
            aliases.update(aggregate_aliases)
        elif re.match(r"(?:sort|order)\b", lowered):
            commands.append(_convert_sort(stage, mapping, errors, aliases))
        elif re.match(r"(?:take|limit)\b", lowered):
            count = re.findall(r"\d+", stage)
            if count:
                commands.append(f"head {count[0]}")
            else:
                errors.append(f"unsupported limit stage: {stage}")
        elif re.match(r"sample\b", lowered):
            count = re.findall(r"\d+", stage)
            if count:
                commands.append(f"head {count[0]}")
            else:
                errors.append(f"unsupported sample stage: {stage}")
        elif re.match(r"count\b", lowered):
            commands.append("stats count as Count")
            aliases.add("Count")
        elif re.match(r"search\b", lowered):
            search_stage = _parse_search_stage(stage)
            if not search_stage:
                errors.append(f"unsupported KQL search stage: {stage}")
                continue
            if search_stage.tables:
                errors.append("unsupported KQL stage: nested search in (...)")
                continue
            predicate, predicate_errors = _convert_search_expression(search_stage.expression, mapping, aliases)
            errors.extend(predicate_errors)
            if predicate:
                if commands:
                    commands.append(f"where {predicate}")
                else:
                    filters.append(f"({predicate})")
        elif re.match(r"top\b", lowered):
            top_commands = _convert_top(stage, mapping, errors, aliases)
            if top_commands:
                commands.extend(top_commands)
            else:
                errors.append(f"unsupported top stage: {stage}")
        elif re.match(r"distinct\b", lowered):
            distinct_clause = re.sub(r"^\s*distinct\b", "", stage, flags=re.IGNORECASE).strip()
            fields_clause = _convert_fields_clause(distinct_clause, mapping, errors, aliases)
            if fields_clause:
                commands.append(f"stats count as Count by {fields_clause}")
                aliases.add("Count")
        elif re.match(r"render\b", lowered):
            continue
        else:
            errors.append(f"unsupported KQL stage: {stage}")

    if errors:
        return "", {}, sorted(set(errors))

    query = " and ".join(filters)
    if commands:
        query = f"{query} | " + " | ".join(commands)
    return query, {
        "tables": tables,
        "sources": sources,
        "category": category,
        "service": service,
    }, []
