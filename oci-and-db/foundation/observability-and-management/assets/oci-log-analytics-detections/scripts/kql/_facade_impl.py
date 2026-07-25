"""KQL→Logan QL converter — facade coordinator.

The converter implementation was originally extracted out of the legacy
``scripts/convert_sentinel_kql.py`` facade (plan 06-10) and lived here as one
monolithic module. Plan T5 redistributed those internals into focused modules
under ``scripts.kql`` (constants, lexical helpers, mapping config, source
extraction, field rendering, predicates, operators, pipeline, validation).

This module is now a thin coordinator: it re-exports the full historical
symbol surface so every existing consumer — ``scripts/convert_sentinel_kql``
and the ``scripts.kql._facade_impl import ...`` callers — keeps working
byte-for-byte. New callers should prefer the focused modules directly.
"""

from __future__ import annotations

# Re-exported for backward compatibility: callers historically imported these
# Sentinel-sync helpers via this module's namespace.
from scripts.sync_sentinel_kql import (  # noqa: F401
    DEFAULT_CACHE_DIR,
    SENTINEL_LICENSE_URL,
    SENTINEL_WEB_URL,
    build_candidate_export,
    load_sentinel_candidates,
    resolve_sentinel_commit,
    sync_sentinel_repo,
)

from scripts.kql._constants import (  # noqa: F401
    AZURE_AUDIT_SCHEMA_FIELDS,
    CONFIG_PATH,
    ConversionResult,
    DEFAULT_CANDIDATES_FILE,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REPORT_PATH,
    ENTITY_ENRICHMENT_ALIASES,
    ENTITY_ENRICHMENT_ALIASES_NORMALIZED,
    FIELD_DICTIONARY_PATH,
    LOGAN_BUILTIN_FIELDS,
    LOGAN_COMMANDS,
    LOGAN_UNSUPPORTED_PATTERNS,
    NUMERIC_FIELD_TYPES,
    PROJECT_DIR,
    SCALAR_CAST_FUNCTIONS,
    SEVERITY_SCORE,
    STRING_FIELD_TYPES,
    SUPPORTED_AGGREGATIONS,
    UNSUPPORTED_PATTERNS,
    SearchStage,
)
from scripts.kql._fields import (  # noqa: F401
    _cleanup_boolean_expression,
    _display_field_name,
    _escape_logan_string,
    _field_is_quoted,
    _field_role,
    _format_value,
    _format_value_for_field,
    _is_allowed_logan_field,
    _literal_value,
    _logan_field_reference,
    _normalize_field_name,
    _record_field_error,
    _remove_time_filters,
    map_field,
)
from scripts.kql._mapping_config import (  # noqa: F401
    _load_field_dictionary_field_types,
    _load_field_dictionary_fields,
    load_mapping_config,
)
from scripts.kql._operators import (  # noqa: F401
    _column_ifexists_field,
    _convert_extend,
    _convert_fields_clause,
    _convert_project,
    _convert_scalar_expression,
    _convert_sort,
    _convert_summarize,
    _convert_top,
    _default_aggregate_alias,
    _find_top_level_binary,
    _function_args,
    _sanitize_alias,
    _span_to_logan,
    _split_alias_expression,
    _split_time_bin,
    _summarize_by_only_clause,
    _unique_alias,
)
from scripts.kql._pipeline import convert_kql_to_logan  # noqa: F401
from scripts.kql._predicates import (  # noqa: F401
    _convert_search_expression,
    _free_text_search_clause,
    _search_expression_looks_like_predicate,
    convert_predicate,
)
from scripts.kql._sources import (  # noqa: F401
    _clean_table_name,
    _extract_union_tables,
    _parse_search_stage,
    _source_filter_for_tables,
    _split_union_operands,
    _strip_search_options,
    _strip_table_extraction_preamble,
    _take_parenthesized_prefix,
    extract_source_tables,
)
from scripts.kql._text_utils import (  # noqa: F401
    _classify_unsupported_kql_text,
    _find_top_level_semicolon,
    _normalize_simple_let_expression,
    _preprocess_simple_lets,
    _replace_unquoted_variables,
    _split_kql_stages,
    _split_top_level,
    _strip_kql_comments,
    _strip_set_directives,
    _strip_single_quoted_literals,
    _strip_string_literals,
    classify_unsupported_kql,
)
from scripts.kql._validation import (  # noqa: F401
    _extract_query_aliases,
    _extract_query_field_references,
    _extract_unquoted_operator_fields,
    _iter_quoted_values,
    _quote_context_indicates_field,
    validate_logan_query_local,
)
