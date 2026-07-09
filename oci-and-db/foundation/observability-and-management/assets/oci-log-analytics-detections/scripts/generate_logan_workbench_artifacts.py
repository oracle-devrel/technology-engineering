#!/usr/bin/env python3
"""Generate OCI Logan workbench reference, pattern, and example artifacts.

The integrated webapp consumes these JSON files. This repository remains the
source of truth for generated conversion guidance and examples.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from analyze_ql_conversion_coverage import build_matrix  # noqa: E402

QUERY_SEARCH_URL = "https://docs.oracle.com/en-us/iaas/log-analytics/doc/query-search.html"
COMMAND_REFERENCE_URL = "https://docs.oracle.com/en-us/iaas/log-analytics/doc/command-reference.html"

REFERENCE_PATH = PROJECT_ROOT / "queries" / "logan_ql_reference_catalog.json"
PATTERNS_PATH = PROJECT_ROOT / "queries" / "cross_ql_mapping_patterns.json"
EXAMPLES_PATH = PROJECT_ROOT / "queries" / "conversion_examples.json"
CAPABILITY_MATRIX_PATH = PROJECT_ROOT / "queries" / "ql_conversion_capability_matrix.json"

REQUIRED_COMMANDS = [
    "search",
    "where",
    "stats",
    "timestats",
    "eval",
    "fields",
    "sort",
    "top",
    "distinct",
    "regex",
    "lookup",
    "link",
    "sequence",
    "rename",
    "head",
]


@dataclass(frozen=True)
class CommandSeed:
    name: str
    category: str
    summary: str
    syntax: str
    examples: list[str]
    notes: list[str]
    source_url: str = COMMAND_REFERENCE_URL


COMMAND_SEEDS = [
    CommandSeed(
        "search",
        "base",
        "Starts an OCI Log Analytics search with source and field predicates.",
        "'Log Source' = '<source>' and 'Field' = 'value'",
        ["'Log Source' = 'OCI Audit Logs' and 'Event Name' = 'ConsoleSignIn'"],
        ["Use quoted display field names for OCI fields that contain spaces."],
        QUERY_SEARCH_URL,
    ),
    CommandSeed(
        "where",
        "filter",
        "Filters the current result set with a boolean expression.",
        "| where <predicate>",
        ["| where attempts > 5 and 'Principal Name' is not null"],
        ["Maps from KQL where, SPL where/search predicates, and Lucene field filters."],
    ),
    CommandSeed(
        "stats",
        "aggregate",
        "Aggregates records and groups by selected dimensions.",
        "| stats count as Count by 'Host Name', 'User Name'",
        ["| stats count as hits by 'Host Name', 'Event Name'"],
        ["Maps from KQL summarize, SPL stats, Elastic aggregations, and Sigma count conditions."],
    ),
    CommandSeed(
        "timestats",
        "aggregate",
        "Aggregates records into time buckets for trend and spike detection.",
        "| timestats span=5m count as failures by src_ip",
        ["| timestats span=5m count as failures by 'Host Name'"],
        ["Prefer timestats when the source query bins or buckets TimeGenerated/_time."],
    ),
    CommandSeed(
        "eval",
        "transform",
        "Calculates a new field from existing fields and expressions.",
        "| eval risk = if(hits > 10, 'high', 'medium')",
        ["| eval src_ip = extract('Message', /from ([0-9.]+)/)"],
        ["Maps from KQL extend/project aliases and SPL eval."],
    ),
    CommandSeed(
        "fields",
        "projection",
        "Keeps or orders the selected fields in the output.",
        "| fields 'Time', 'Host Name', 'User Name'",
        ["| fields 'Time', 'Computer', 'Command Line'"],
        ["Maps from KQL project, SPL table/fields, and Elastic selected columns."],
    ),
    CommandSeed(
        "sort",
        "ordering",
        "Sorts the current result set by one or more fields.",
        "| sort -hits",
        ["| sort -Count | head 100"],
        ["Prefix a field with '-' for descending order and cap broad result sets with head."],
    ),
    CommandSeed(
        "top",
        "aggregate",
        "Returns the most frequent values for a field or aggregation.",
        "| top 20 'Source IP'",
        ["| top 10 'Event Name'"],
        ["Use stats plus sort when the source query needs multi-field ranking."],
    ),
    CommandSeed(
        "distinct",
        "aggregate",
        "Returns unique values for selected fields.",
        "| distinct 'Host Name', 'User Name'",
        ["| distinct 'Principal Name'"],
        ["Maps from KQL distinct and SPL dedup/table patterns."],
    ),
    CommandSeed(
        "regex",
        "extract",
        "Matches or extracts values with a regular expression where supported by Logan QL.",
        "| regex 'Message' = /Failed password/",
        ["| eval src_ip = extract('Message', /from ([0-9.]+)/)"],
        ["Prefer documented extraction functions when the goal is creating a new field."],
    ),
    CommandSeed(
        "lookup",
        "enrichment",
        "Invokes a field-value lookup for enrichment or filtering.",
        "| lookup <lookup_name> <field>",
        ["[searchlookup table=ip_blacklist | distinct ip] | timestats count"],
        ["Sentinel watchlists and Splunk lookups need an explicit OCI lookup/table design."],
    ),
    CommandSeed(
        "link",
        "correlation",
        "Groups related log records into transaction-style linked events.",
        "| link 'Host Name', 'User Name'",
        ["| link 'Host Name' | stats count as Events"],
        ["Elastic EQL sequence conversion should use link groups when a stable entity field exists."],
    ),
    CommandSeed(
        "sequence",
        "correlation",
        "Identifies ordered event patterns inside linked event groups.",
        "| link 'Host Name' | sequence 'Event Name' = 'start', 'Event Name' = 'stop'",
        ["| link 'Host Name' | sequence 'Event ID' = '4624', 'Event ID' = '4688'"],
        ["Only convert source sequence semantics when the ordering, grouping key, and time span are preserved."],
    ),
    CommandSeed(
        "rename",
        "projection",
        "Renames output fields for downstream display or grouping.",
        "| rename 'User Name' as user",
        ["| rename ip as 'host address'"],
        ["Maps from SPL rename and KQL project aliases when the conversion is lossless."],
    ),
    CommandSeed(
        "head",
        "ordering",
        "Limits the result set to the first N rows.",
        "| head 100",
        ["| sort -hits | head 50"],
        ["Use with sort/top conversions to keep UI and saved-search results bounded."],
    ),
]


class CommandReferenceParser(HTMLParser):
    """Small parser for the official command-reference table."""

    def __init__(self) -> None:
        super().__init__()
        self.rows: list[dict[str, str]] = []
        self._in_td = False
        self._td_index = -1
        self._row_cells: list[str] = []
        self._buf: list[str] = []
        self._href = ""
        self._current_href = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key: value or "" for key, value in attrs}
        if tag == "tr":
            self._row_cells = []
            self._td_index = -1
        elif tag == "td":
            self._in_td = True
            self._td_index += 1
            self._buf = []
            self._href = ""
        elif tag == "a" and self._in_td:
            self._current_href = attrs_dict.get("href", "")
            if not self._href:
                self._href = self._current_href

    def handle_endtag(self, tag: str) -> None:
        if tag == "td" and self._in_td:
            self._row_cells.append(" ".join("".join(self._buf).split()))
            self._in_td = False
            self._buf = []
        elif tag == "tr" and len(self._row_cells) >= 2:
            command = self._row_cells[0].strip()
            description = self._row_cells[1].strip()
            if re.fullmatch(r"[a-z][a-z0-9_-]*", command):
                self.rows.append({"command": command, "description": description, "href": self._href})
        elif tag == "a":
            self._current_href = ""

    def handle_data(self, data: str) -> None:
        if self._in_td:
            self._buf.append(data)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def fetch_url(url: str) -> str:
    request = Request(url, headers={"User-Agent": "oci-logan-workbench-artifact-generator/1.0"})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_official_commands(html: str) -> dict[str, dict[str, str]]:
    parser = CommandReferenceParser()
    parser.feed(html)
    return {row["command"]: row for row in parser.rows}


def build_reference_catalog(refresh_docs: bool) -> dict:
    retrieved_at = now_iso()
    official: dict[str, dict[str, str]] = {}
    fetch_error = ""
    if refresh_docs:
        try:
            official = parse_official_commands(fetch_url(COMMAND_REFERENCE_URL))
        except (OSError, URLError, TimeoutError) as exc:
            fetch_error = str(exc)

    entries = []
    for seed in COMMAND_SEEDS:
        official_row = official.get(seed.name, {})
        source_path = official_row.get("href") or f"{seed.name}.html"
        source_url = seed.source_url
        if seed.source_url == COMMAND_REFERENCE_URL and source_path:
            source_url = f"https://docs.oracle.com/en-us/iaas/log-analytics/doc/{source_path}"
        official_summary = official_row.get("description") or seed.summary
        entries.append(
            {
                "name": seed.name,
                "category": seed.category,
                "source_url": source_url,
                "source_title": "OCI Log Analytics Query Language Command Reference",
                "retrieved_at": retrieved_at,
                "summary": official_summary,
                "syntax": seed.syntax,
                "examples": seed.examples,
                "notes": seed.notes,
                "provenance": {
                    "official_command_reference": COMMAND_REFERENCE_URL,
                    "official_query_search": QUERY_SEARCH_URL,
                    "generated_by": "scripts/generate_logan_workbench_artifacts.py",
                    "live_fetch": bool(official),
                    "fetch_error": fetch_error,
                },
            }
        )

    return {
        "schema_version": "1.0.0",
        "generated_at": retrieved_at,
        "sources": [QUERY_SEARCH_URL, COMMAND_REFERENCE_URL],
        "required_commands": REQUIRED_COMMANDS,
        "commands": entries,
    }


def build_patterns() -> dict:
    generated_at = now_iso()
    patterns = [
        {
            "id": "spl-filter-to-search-where",
            "source_language": "splunk_spl",
            "source_construct": "search predicates, index, sourcetype, where",
            "oci_mapping": "Use a Logan base search for log source constraints and pipe into where for derived predicates.",
            "support_level": "supported",
            "logan_commands": ["search", "where"],
            "warning_behavior": "Warn when SPL macros, subsearches, or accelerated data models are present.",
            "example_ids": ["spl-powershell-encoded"],
        },
        {
            "id": "kql-where-summarize",
            "source_language": "sentinel_kql",
            "source_construct": "where + summarize/count/bin",
            "oci_mapping": "Map table names to OCI Log Sources, predicates to search/where, summarize to stats, and bin(TimeGenerated) to timestats span.",
            "support_level": "supported",
            "logan_commands": ["search", "where", "stats", "timestats"],
            "warning_behavior": "Block unsupported joins, watchlists, dynamic bag expansion, and regex extraction unless explicitly mapped.",
            "example_ids": ["kql-securityevent-powershell", "kql-audit-no-mfa"],
        },
        {
            "id": "kql-search-in",
            "source_language": "sentinel_kql",
            "source_construct": "search in (...) free-text terms and table-scoped search predicates",
            "oci_mapping": "Map KQL search table scopes to OCI Log Sources and free-text terms to Original Log Content/msg predicates.",
            "support_level": "supported",
            "logan_commands": ["search", "where", "head"],
            "warning_behavior": "Require mapped in (...) tables for first-stage search and warn through validation when a searched field is not mapped.",
            "example_ids": ["kql-search-contoso"],
        },
        {
            "id": "kql-common-operators",
            "source_language": "sentinel_kql",
            "source_construct": "where, between, extend/case, summarize by, sort, take/count",
            "oci_mapping": "Strip explicit KQL time windows, map predicates to OCI display fields, use eval for scalar classification, stats for count/distinct rollups, sort -field for Kusto's default descending order, and head for take/limit.",
            "support_level": "supported",
            "logan_commands": ["search", "where", "eval", "stats", "sort", "head"],
            "warning_behavior": "Warn through validation when projected or calculated fields are not backed by the mapping allow-list.",
            "example_ids": ["kql-common-securityevent-outcomes"],
        },
        {
            "id": "sigma-selection-condition",
            "source_language": "sigma_yaml",
            "source_construct": "logsource + detection selections + condition",
            "oci_mapping": "Use configured Sigma field and logsource mappings, preserving MITRE/STIG metadata in the response.",
            "support_level": "supported",
            "logan_commands": ["search", "where"],
            "warning_behavior": "Warn on aggregation/timeframe conditions and unmapped fields; refuse unsafe YAML tags.",
            "example_ids": ["sigma-powershell-encoded", "sigma-soc-xss"],
        },
        {
            "id": "elastic-field-query",
            "source_language": "elastic_lucene",
            "source_construct": "field:value, boolean operators, wildcard terms",
            "oci_mapping": "Map ECS-style fields to OCI display fields and translate wildcard values to Logan like predicates.",
            "support_level": "partial",
            "logan_commands": ["search", "where"],
            "warning_behavior": "Warn on nested documents, scripted fields, analyzers, and sequence semantics.",
            "example_ids": ["elastic-powershell-process", "elastic-web-xss"],
        },
        {
            "id": "elastic-kuery-field-query",
            "source_language": "elastic_kuery",
            "source_construct": "Kibana KQL field comparisons, boolean operators, wildcard terms, and existence checks",
            "oci_mapping": "Map ECS field predicates to OCI display fields, preserving supported bool groups and surfacing unsupported nested/analyzed behavior.",
            "support_level": "partial",
            "logan_commands": ["search", "where"],
            "warning_behavior": "Warn on nested objects, analyzer-specific token behavior, scripted fields, and unmapped ECS fields.",
            "example_ids": ["elastic-kuery-http-post-403"],
        },
        {
            "id": "elastic-esql-pipeline",
            "source_language": "elastic_esql",
            "source_construct": "FROM, WHERE, STATS, EVAL, KEEP, SORT, LIMIT",
            "oci_mapping": "Map ES|QL sources to OCI log sources, filters to search/where, aggregations to stats/timestats, projections to fields, and limits to head.",
            "support_level": "partial",
            "logan_commands": ["search", "where", "eval", "stats", "fields", "sort", "head"],
            "warning_behavior": "Warn or block unsupported ES|QL functions such as enrich, mv_expand, fuzzy match, or cross-source joins.",
            "example_ids": ["elastic-esql-http-errors"],
        },
        {
            "id": "elastic-toml-dispatch",
            "source_language": "elastic_toml",
            "source_construct": "Elastic detection rule TOML with rule.type and rule.language",
            "oci_mapping": "Parse metadata, dispatch query/eql/esql rules to language converters, and model threshold/new_terms/threat_match/ML dependencies explicitly.",
            "support_level": "partial",
            "logan_commands": ["search", "where", "stats", "lookup"],
            "warning_behavior": "Never persist third-party rule bodies; return converted output only for the request and surface rule-type dependencies.",
            "example_ids": ["elastic-toml-synthetic-threshold"],
        },
        {
            "id": "lookup-watchlist",
            "source_language": "cross_ql",
            "source_construct": "Splunk lookup, Sentinel _GetWatchlist, Elastic enrich",
            "oci_mapping": "Use OCI lookup/searchlookup artifacts and explicit lookup command design; do not silently inline external lists.",
            "support_level": "lossy",
            "logan_commands": ["lookup"],
            "warning_behavior": "Emit lossy_lookup warning with the required lookup/table name.",
            "example_ids": ["spl-threat-ip-lookup"],
        },
        {
            "id": "join-correlation",
            "source_language": "cross_ql",
            "source_construct": "joins, transactions, sequences, correlations",
            "oci_mapping": "Prefer source-side parser enrichment or dashboard-level correlation. Only convert simple same-source aggregations.",
            "support_level": "unsupported",
            "logan_commands": ["stats"],
            "warning_behavior": "Block true cross-table joins and sequence semantics with unsupported_join_or_sequence.",
            "example_ids": ["kql-unsupported-join"],
        },
        {
            "id": "stateful-or-content-scan-languages",
            "source_language": "cross_ql",
            "source_construct": "OSQuery SQL endpoint-state queries and raw YARA file-content rules",
            "oci_mapping": "Convert only result-log detections when an OCI parser emits OSQuery or YARA result events; do not pretend Logan QL can execute endpoint SQL or scan file bytes.",
            "support_level": "unsupported",
            "logan_commands": ["search", "where"],
            "warning_behavior": "Emit unsupported_stateful_query or unsupported_content_scan unless the input is a result-log query shape.",
            "example_ids": ["osquery-sql-process-result", "yara-result-log"],
        },
        {
            "id": "projection-rename",
            "source_language": "cross_ql",
            "source_construct": "project/table/fields/rename",
            "oci_mapping": "Use fields for projection and rename for display aliases where the source semantics are lossless.",
            "support_level": "supported",
            "logan_commands": ["fields", "rename"],
            "warning_behavior": "Warn when projected fields are not present in the source parser contract.",
            "example_ids": ["kql-project-fields"],
        },
        {
            "id": "sort-limit-top",
            "source_language": "cross_ql",
            "source_construct": "sort, order, head, limit, top",
            "oci_mapping": "Use sort with '-' for descending order and head to cap result sets; use top for single-field high-frequency queries.",
            "support_level": "supported",
            "logan_commands": ["sort", "head", "top"],
            "warning_behavior": "Warn when source query has no explicit cap and generated result could be broad.",
            "example_ids": ["spl-powershell-encoded"],
        },
    ]
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "patterns": patterns,
    }


def build_examples() -> dict:
    generated_at = now_iso()
    examples = [
        {
            "id": "sigma-powershell-encoded",
            "title": "Sigma PowerShell Encoded Command",
            "source_language": "sigma_yaml",
            "source_query": "title: PowerShell Encoded Command\nid: demo-sigma-ps-001\nlogsource:\n  product: windows\n  category: process_creation\ndetection:\n  selection:\n    Image|endswith: '\\\\powershell.exe'\n    CommandLine|contains:\n      - ' -enc '\n      - ' -EncodedCommand '\n  condition: selection\nlevel: high\ntags:\n  - attack.execution\n  - attack.t1059.001",
            "expected_logan_ql": "('Log Source' = 'Windows Sysmon Events' or 'Log Source' = 'Windows Sysmon Operational Logs' or 'Log Source' = 'SOC Windows Sysmon Logs') and (('Process Name' like '*\\\\powershell.exe') and ('Command Line' like '* -enc *' or 'Command Line' like '* -EncodedCommand *'))",
            "explanation": "Sigma logsource and field modifiers map through config/sigma_oci_mapping.yaml into OCI display fields.",
            "warnings": [],
            "support_level": "supported",
            "synthetic_log_shape": "Windows Sysmon Events with Event ID 1, Process Name, Command Line, User Name.",
            "pattern_ids": ["sigma-selection-condition"],
        },
        {
            "id": "kql-securityevent-powershell",
            "title": "Sentinel KQL SecurityEvent PowerShell",
            "source_language": "sentinel_kql",
            "source_query": "SecurityEvent\n| where EventID == 4688\n| where CommandLine has \" -enc \"\n| summarize Hits=count() by Computer, SubjectUserName\n| order by Hits desc",
            "expected_logan_ql": "('Log Source' = 'Windows Security Events' or 'Log Source' = 'Windows Event Security Logs') and ('Event ID' = '4688') and ('Command Line' like '* -enc *') | stats count as Hits by Entity, 'Subject User Name' | sort -Hits",
            "explanation": "The Sentinel table maps to Windows security log sources, has maps to like, and summarize maps to stats.",
            "warnings": [],
            "support_level": "supported",
            "synthetic_log_shape": "Windows Security Events with Event ID 4688 and Command Line.",
            "pattern_ids": ["kql-where-summarize"],
        },
        {
            "id": "kql-search-contoso",
            "title": "KQL Search Across Perf Event Alert",
            "source_language": "sentinel_kql",
            "source_query": "search in (Perf, Event, Alert) \"Contoso\"\n| take 10",
            "expected_logan_ql": "('Log Source' = 'SOC Application Logs' or 'Log Source' = 'Windows Event System Logs' or 'Log Source' = 'Windows Security Events' or 'Log Source' = 'OCI Cloud Guard Problems') and (('Original Log Content' like '*Contoso*' or msg like '*Contoso*')) | head 10",
            "explanation": "KQL search table scopes resolve to mapped OCI sources, and free-text search terms use common raw-message fields.",
            "warnings": [],
            "support_level": "supported",
            "synthetic_log_shape": "SOC Application Logs plus Windows Event and alert-shaped logs with raw message text.",
            "pattern_ids": ["kql-search-in", "sort-limit-top"],
        },
        {
            "id": "kql-common-securityevent-outcomes",
            "title": "KQL Common Operators SecurityEvent Outcomes",
            "source_language": "sentinel_kql",
            "source_query": "SecurityEvent\n| where TimeGenerated between (ago(1d) .. now())\n| where EventID in (4624, 4625)\n| extend Outcome = case(EventID == 4625, 'failed', EventID == 4624, 'success', 'other')\n| summarize by Computer, Outcome\n| sort by Count\n| take 20",
            "expected_logan_ql": "('Log Source' = 'Windows Security Events' or 'Log Source' = 'Windows Event Security Logs') and ('Event ID' in ('4624', '4625')) | eval Outcome = if('Event ID' = '4625', 'failed', if('Event ID' = '4624', 'success', 'other')) | stats count as Count by Entity, Outcome | sort -Count | head 20",
            "explanation": "Common KQL operators map to Logan filters and pipeline commands: explicit time windows are delegated to the dashboard range, case becomes eval/if, summarize-by becomes a counted distinct rollup, and take becomes head.",
            "warnings": [],
            "support_level": "supported",
            "synthetic_log_shape": "Windows Security Events with Event ID, host entity, and outcome classification.",
            "pattern_ids": ["kql-common-operators", "sort-limit-top"],
        },
        {
            "id": "spl-powershell-encoded",
            "title": "Splunk SPL Encoded PowerShell",
            "source_language": "splunk_spl",
            "source_query": "index=windows sourcetype=WinEventLog:Sysmon EventCode=1 Image=\"*\\\\powershell.exe\" CommandLine=\"* -enc *\" | stats count by host User CommandLine | sort -count",
            "expected_logan_ql": "'Log Source' = 'Windows Sysmon Events' and 'Event ID' = '1' and 'Process Name' like '*\\\\powershell.exe' and 'Command Line' like '* -enc *' | stats count as count by 'Host Name', 'User Name', 'Command Line' | sort -count | head 100",
            "explanation": "SPL source constraints become the Logan base search; stats/sort are retained as pipe commands.",
            "warnings": ["SPL conversion is heuristic unless a backend parser plugin is configured."],
            "support_level": "partial",
            "synthetic_log_shape": "Windows Sysmon Events with host, user, process, and command line fields.",
            "pattern_ids": ["spl-filter-to-search-where", "sort-limit-top"],
        },
        {
            "id": "elastic-powershell-process",
            "title": "Elastic Lucene PowerShell Process",
            "source_language": "elastic_lucene",
            "source_query": "event.code:1 AND process.name:powershell.exe AND process.command_line:(*enc* OR *EncodedCommand*)",
            "expected_logan_ql": "'Log Source' = 'Windows Sysmon Events' and 'Event ID' = '1' and 'Process Name' like '*powershell.exe' and ('Command Line' like '*enc*' or 'Command Line' like '*EncodedCommand*') | head 100",
            "explanation": "ECS process fields map to OCI process display fields and wildcard terms map to like predicates.",
            "warnings": ["Analyzer and nested-document behavior are not represented in Logan QL."],
            "support_level": "partial",
            "synthetic_log_shape": "Windows Sysmon Events with ECS-like process fields mapped by parser.",
            "pattern_ids": ["elastic-field-query"],
        },
        {
            "id": "elastic-kuery-http-post-403",
            "title": "Elastic Kuery HTTP POST 403",
            "source_language": "elastic_kuery",
            "source_query": "http.response.status_code:403 and http.request.method:post",
            "expected_logan_ql": "'Log Source' = 'SOC Application Logs' and 'Response Code' = 403 and 'Request Method' = 'POST' | stats count as hits by 'Service Name', 'Trace ID', 'Source IP' | sort -hits | head 100",
            "explanation": "Self-authored Kuery example mapping ECS HTTP fields to SOC Application Logs display fields.",
            "warnings": ["Analyzer-specific KQL behavior is not represented in Logan QL."],
            "support_level": "partial",
            "synthetic_log_shape": "SOC Application Logs with Response Code, Request Method, Service Name, Trace ID, and Source IP.",
            "pattern_ids": ["elastic-kuery-field-query"],
        },
        {
            "id": "elastic-esql-http-errors",
            "title": "Elastic ES|QL HTTP Error Rollup",
            "source_language": "elastic_esql",
            "source_query": "FROM logs-apm*\n| WHERE http.response.status_code >= 500 and service.name is not null\n| STATS errors = count(*) BY service.name\n| SORT errors DESC\n| LIMIT 20",
            "expected_logan_ql": "'Log Source' = 'SOC Application Logs' and 'Response Code' >= 500 and 'Service Name' is not null | stats count as errors by 'Service Name' | sort -errors | head 20",
            "explanation": "Self-authored ES|QL pipeline example mapping FROM/WHERE/STATS/SORT/LIMIT into Logan QL.",
            "warnings": ["Only common ES|QL pipeline commands are converted in the first implementation tranche."],
            "support_level": "partial",
            "synthetic_log_shape": "SOC Application Logs with Response Code and Service Name.",
            "pattern_ids": ["elastic-esql-pipeline"],
        },
        {
            "id": "elastic-toml-synthetic-threshold",
            "title": "Elastic TOML Synthetic Threshold",
            "source_language": "elastic_toml",
            "source_query": "[rule]\ntype = \"threshold\"\nlanguage = \"kuery\"\nname = \"Synthetic failed authentication threshold\"\nquery = '''event.category:authentication and event.outcome:failure'''\n\n[rule.threshold]\nfield = [\"source.ip\", \"user.name\"]\nvalue = 5",
            "expected_logan_ql": "'Log Source' = 'OCI Audit Logs' and 'Original Log Content' like '*authentication*' and Status = 'failure' | stats count as event_count by 'Source IP', 'User Name' | where event_count >= 5 | head 100",
            "explanation": "Self-authored Elastic-style TOML threshold example dispatching metadata to the Kuery converter and threshold aggregation path.",
            "warnings": ["Threshold windows and schedules must be validated against the OCI saved-search schedule."],
            "support_level": "lossy",
            "synthetic_log_shape": "OCI Audit Logs with Source IP, User Name, Event Category, and Status fields.",
            "pattern_ids": ["elastic-toml-dispatch"],
        },
        {
            "id": "sigma-soc-xss",
            "title": "Sigma SOC Application XSS",
            "source_language": "sigma_yaml",
            "source_query": "title: Reflected XSS In Browser Telemetry\nid: demo-sigma-xss-001\nlogsource:\n  product: web\ndetection:\n  selection:\n    url|contains:\n      - '<script'\n      - 'javascript:'\n  condition: selection\nlevel: high\ntags:\n  - attack.initial_access",
            "expected_logan_ql": "'Log Source' = 'SOC Application Logs' and (('Request URL' like '*<script*' or 'Request URL' like '*javascript:*'))",
            "explanation": "The app/APM parser exposes Request URL and Trace ID on SOC Application Logs.",
            "warnings": [],
            "support_level": "supported",
            "synthetic_log_shape": "SOC Application Logs OpenTelemetry-shaped JSON with Request URL and Trace ID.",
            "pattern_ids": ["sigma-selection-condition"],
        },
        {
            "id": "kql-audit-no-mfa",
            "title": "Sentinel Audit Sign-In Without MFA",
            "source_language": "sentinel_kql",
            "source_query": "AuditLogs\n| where OperationName == \"UserLoggedIn\"\n| where Result == \"success\"\n| summarize Attempts=count() by OperationName, Result\n| order by Attempts desc",
            "expected_logan_ql": "'Log Source' = 'Azure Entra ID Audit Logs' and (Operation = 'UserLoggedIn') and (Status = 'success') | stats count as Attempts by Operation, Status | sort -Attempts",
            "explanation": "Cloud audit table predicates map to audit source fields and aggregate by supported operation/status fields.",
            "warnings": [],
            "support_level": "supported",
            "synthetic_log_shape": "Cloud audit log with operation, status, target resource, and principal.",
            "pattern_ids": ["kql-where-summarize"],
        },
        {
            "id": "elastic-web-xss",
            "title": "Elastic Web XSS",
            "source_language": "elastic_lucene",
            "source_query": "url.path:*search* AND url.query:(*<script* OR *onerror*) AND http.response.status_code:200",
            "expected_logan_ql": "'Log Source' = 'SOC Application Logs' and 'Request URL' like '*search*' and ('Request URL' like '*<script*' or 'Request URL' like '*onerror*') and 'Response Code' = 200 | stats count as hits by 'Service Name', 'Trace ID', 'Source IP' | sort -hits",
            "explanation": "HTTP URL and response fields map to SOC Application Logs display fields.",
            "warnings": ["Escaping behavior depends on the parser-normalized request URL."],
            "support_level": "partial",
            "synthetic_log_shape": "SOC Application Logs with Request URL, Response Code, Source IP.",
            "pattern_ids": ["elastic-field-query"],
        },
        {
            "id": "spl-threat-ip-lookup",
            "title": "Splunk Threat IP Lookup",
            "source_language": "splunk_spl",
            "source_query": "index=network src_ip=* | lookup threat_ips ip as src_ip OUTPUT threat | where isnotnull(threat) | stats count by src_ip threat",
            "expected_logan_ql": "'Log Source' = 'OCI VCN Flow Logs' | lookup threat_ips 'Source IP' | where threat is not null | stats count as count by 'Source IP', threat",
            "explanation": "Lookups require a pre-created OCI lookup table; the frontend must surface that dependency.",
            "warnings": ["lossy_lookup: requires OCI lookup table threat_ips"],
            "support_level": "lossy",
            "synthetic_log_shape": "VCN flow logs with Source IP plus an OCI lookup table named threat_ips.",
            "pattern_ids": ["lookup-watchlist"],
        },
        {
            "id": "kql-unsupported-join",
            "title": "Sentinel Unsupported Cross-Table Join",
            "source_language": "sentinel_kql",
            "source_query": "SecurityEvent\n| join kind=inner (SigninLogs) on Account\n| summarize count() by Account",
            "expected_logan_ql": "",
            "explanation": "True cross-table joins are blocked until a backend correlation strategy exists.",
            "warnings": ["unsupported_join_or_sequence"],
            "support_level": "unsupported",
            "synthetic_log_shape": "Requires multiple source tables; not represented by one Logan query.",
            "pattern_ids": ["join-correlation"],
        },
        {
            "id": "osquery-sql-process-result",
            "title": "OSQuery SQL Endpoint State Boundary",
            "source_language": "osquery_sql",
            "source_query": "select name, cmdline from processes where name = 'powershell.exe';",
            "expected_logan_ql": "",
            "explanation": "OSQuery SQL runs on endpoint state, so Logan Forge only converts OSQuery result logs, not raw endpoint SQL execution.",
            "warnings": ["unsupported_stateful_query"],
            "support_level": "unsupported",
            "synthetic_log_shape": "Requires an OSQuery result log source before Logan QL can search results.",
            "pattern_ids": ["stateful-or-content-scan-languages"],
        },
        {
            "id": "yara-result-log",
            "title": "YARA Content Scan Boundary",
            "source_language": "yara",
            "source_query": "rule SuspiciousString { strings: $a = \"Invoke-Expression\" condition: $a }",
            "expected_logan_ql": "",
            "explanation": "YARA scans file content; Logan Forge converts YARA match result logs only when a real OCI log source emits those events.",
            "warnings": ["unsupported_content_scan"],
            "support_level": "unsupported",
            "synthetic_log_shape": "Requires a YARA match result log source before Logan QL can search matches.",
            "pattern_ids": ["stateful-or-content-scan-languages"],
        },
        {
            "id": "oci-passthrough-top-errors",
            "title": "OCI Logan QL Passthrough",
            "source_language": "oci_logan",
            "source_query": "'Log Source' = 'SOC Application Logs' and 'Response Code' >= 500 | stats count as errors by 'Service Name' | sort -errors | head 20",
            "expected_logan_ql": "'Log Source' = 'SOC Application Logs' and 'Response Code' >= 500 | stats count as errors by 'Service Name' | sort -errors | head 20",
            "explanation": "OCI Logan QL inputs pass through with validation and contextual docs.",
            "warnings": [],
            "support_level": "supported",
            "synthetic_log_shape": "SOC Application Logs with Response Code and Service Name.",
            "pattern_ids": ["sort-limit-top"],
        },
    ]
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "examples": examples,
    }


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Logan conversion workbench artifacts")
    parser.add_argument("--refresh-docs", action="store_true", help="Fetch official Oracle docs for command provenance")
    parser.add_argument("--elastic-repo", type=Path, help="Optional local elastic/detection-rules checkout for aggregate counts")
    args = parser.parse_args()

    write_json(REFERENCE_PATH, build_reference_catalog(refresh_docs=args.refresh_docs))
    write_json(PATTERNS_PATH, build_patterns())
    write_json(EXAMPLES_PATH, build_examples())
    write_json(CAPABILITY_MATRIX_PATH, build_matrix(args.elastic_repo))
    print(f"wrote {REFERENCE_PATH.relative_to(PROJECT_ROOT)}")
    print(f"wrote {PATTERNS_PATH.relative_to(PROJECT_ROOT)}")
    print(f"wrote {EXAMPLES_PATH.relative_to(PROJECT_ROOT)}")
    print(f"wrote {CAPABILITY_MATRIX_PATH.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
