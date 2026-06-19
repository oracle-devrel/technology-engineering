"""Shared constants and result dataclasses for the KQL→Logan QL converter.

Extracted from ``scripts/kql/_facade_impl.py`` (plan T5) without behavior
change. Holds path constants, field/aggregation lookup tables, the
unsupported-construct pattern lists, and the two frozen result dataclasses.
The ``_facade_impl`` coordinator re-exports every public name here so the
historical import surface is preserved byte-for-byte.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_DIR / "config" / "sentinel_oci_mapping.yaml"
DEFAULT_CANDIDATES_FILE = PROJECT_DIR / "queries" / "sentinel_candidates.json"
DEFAULT_OUTPUT_DIR = PROJECT_DIR / "queries" / "sentinel"
DEFAULT_REPORT_PATH = PROJECT_DIR / "queries" / "sentinel_conversion_report.json"
FIELD_DICTIONARY_PATH = PROJECT_DIR / "queries" / "log_source_field_dictionary.json"

LOGAN_BUILTIN_FIELDS = {
    "Channel",
    "Count",
    "Entity",
    "Event Type",
    "Image",
    "Log Source",
    "Original Log Content",
    "Provider",
    "Resource Name",
    "Severity",
    "Status",
    "Time",
    "Type",
    "User",
    "User Name",
    "msg",
    "time",
}

AZURE_AUDIT_SCHEMA_FIELDS = {
    "App Name",
    "Client IP",
    "Correlation ID",
    "Event Name",
    "Operation",
    "Resource Group",
    "Resource Provider",
    "Subscription ID",
    "Target Type",
    "Target UPN",
    "Tenant ID",
    "Workload",
}

LOGAN_COMMANDS = {
    "and",
    "as",
    "by",
    "count",
    "distinctcount",
    "eval",
    "fields",
    "head",
    "in",
    "like",
    "not",
    "or",
    "rename",
    "sort",
    "span",
    "stats",
    "where",
}

ENTITY_ENRICHMENT_ALIASES = {
    "AccountName",
    "AccountCustomEntity",
    "AccountNTDomain",
    "AccountUPNSuffix",
    "Account_0_Name",
    "Account_0_NTDomain",
    "DnsDomain",
    "DNSCustomEntity",
    "DnsCustomEntity",
    "DomainIndex",
    "FileCustomEntity",
    "HostName",
    "HostNameDomain",
    "HostCustomEntity",
    "Host_0_DnsDomain",
    "Host_0_HostName",
    "IPCustomEntity",
    "IpCustomEntity",
    "IP_0_Address",
    "MalwareCustomEntity",
    "Name",
    "NTDomain",
    "URLCustomEntity",
    "UrlCustomEntity",
}

ENTITY_ENRICHMENT_ALIASES_NORMALIZED = {
    alias.lower() for alias in ENTITY_ENRICHMENT_ALIASES
}

SEVERITY_SCORE = {
    "critical": 40,
    "high": 35,
    "medium": 25,
    "low": 10,
    "informational": 5,
    "info": 5,
}

SUPPORTED_AGGREGATIONS = {
    "count": "count",
    "dcount": "distinctcount",
    "distinctcount": "distinctcount",
    "sum": "sum",
    "min": "min",
    "max": "max",
    "avg": "avg",
    "average": "average",
    "make_list": "unique",
    "makelist": "unique",
    "make_set": "unique",
    "makeset": "unique",
    "take_any": "unique",
    "any": "unique",
}

NUMERIC_FIELD_TYPES = {
    "DECIMAL",
    "DOUBLE",
    "FLOAT",
    "INTEGER",
    "LONG",
    "NUMBER",
    "SHORT",
}

STRING_FIELD_TYPES = {
    "STRING",
    "TEXT",
}

# KQL type-cast scalar functions that lower to a no-op in Logan QL's
# loosely typed ``eval`` context. Unwrapping them to the inner expression is
# lossless: Logan applies the same string/numeric/boolean coercion at compare
# and render time regardless of the cast wrapper. Kept as a single source of
# truth so the scalar converter and the predicate cast-unwrap pass agree.
SCALAR_CAST_FUNCTIONS = (
    "tostring",
    "toint",
    "tolong",
    "todouble",
    "toreal",
    "tofloat",
    "todecimal",
    "tobool",
    "toboolean",
)

UNSUPPORTED_PATTERNS = [
    (re.compile(r"\bjoin\b", re.IGNORECASE), "unsupported KQL operator: join"),
    (re.compile(r"\blet\s+\w+\s*=", re.IGNORECASE), "unsupported KQL construct: let variables"),
    (re.compile(r"\bmake-series\b", re.IGNORECASE), "unsupported KQL operator: make-series"),
    (re.compile(r"\bmv-(?:expand|apply)\b", re.IGNORECASE), "unsupported KQL operator: mv-expand/mv-apply"),
    (re.compile(r"\bdatatable\s*\(", re.IGNORECASE), "unsupported KQL construct: datatable"),
    (re.compile(r"\bexternaldata\s*\(", re.IGNORECASE), "unsupported KQL construct: externaldata"),
    (re.compile(r"\b_?GetWatchlist\s*\(", re.IGNORECASE), "unsupported KQL construct: watchlists"),
    (re.compile(r"\bwatchlist\b", re.IGNORECASE), "unsupported KQL construct: watchlists"),
    (re.compile(r"\binvoke\b", re.IGNORECASE), "unsupported KQL construct: custom function invocation"),
    (re.compile(r"\bevaluate\b", re.IGNORECASE), "unsupported KQL operator: evaluate"),
    (re.compile(r"\bparse_command_line\s*\(", re.IGNORECASE), "unsupported KQL function: parse_command_line"),
    (re.compile(r"\|\s*parse(?:-where)?\b", re.IGNORECASE), "unsupported KQL operator: parse"),
    # ``materialize``, ``strlen``, ``strcat`` and ``extract`` are translated by
    # ``_convert_scalar_expression`` (Phase 9 operator-parity tranche); they are
    # no longer whole-query blockers. ``extract_all`` (multi-match) stays
    # unsupported because Logan ``extract`` returns a single match.
    (re.compile(r"\b(parse_json|todynamic|bag_unpack|bag_keys|extractjson)\s*\(", re.IGNORECASE), "unsupported KQL JSON bag expansion"),
    (re.compile(r"\bextract_all\s*\(", re.IGNORECASE), "unsupported KQL regex extraction (extract_all)"),
    (re.compile(r"\bmatches\s+regex\b", re.IGNORECASE), "unsupported KQL regex predicate"),
    (re.compile(r"\[[^\]]+\]\."), "unsupported KQL JSON/index path"),
]

LOGAN_UNSUPPORTED_PATTERNS = [
    re.compile(r"\b(?:summarize|project|extend|join|let|datatable|externaldata|make-series)\b", re.IGNORECASE),
    re.compile(r"\b(?:has|has_any|has_all|hasprefix|hassuffix|contains|startswith|endswith)\b", re.IGNORECASE),
    re.compile(r"\b(?:TimeGenerated|Timestamp|DeviceId)\b", re.IGNORECASE),
    re.compile(r"\bago\s*\(", re.IGNORECASE),
    re.compile(r"\b(?:bin|strlen|tolower|toupper|tostring|parse_json|toint|int)\s*\(", re.IGNORECASE),
    re.compile(r"==|=~|!~"),
    re.compile(r"\{\{|\}\}"),
]


@dataclass(frozen=True)
class ConversionResult:
    """Result for one Sentinel candidate conversion attempt."""

    candidate: dict
    query_payload: dict | None
    skip_reasons: list[str]
    local_validation_errors: list[str]
    live_validation_result: dict | None = None
    output_file: str = ""

    @property
    def promoted_candidate(self) -> bool:
        return self.query_payload is not None and not self.skip_reasons and not self.local_validation_errors


@dataclass(frozen=True)
class SearchStage:
    """Parsed KQL search operator source scope and expression."""

    tables: list[str]
    expression: str
