#!/usr/bin/env python3
"""Backend conversion wrapper for the Logan Forge frontend.

The wrapper reads one JSON request from stdin and writes one JSON response to
stdout.  It intentionally performs no writes and shells out to nothing; callers
should execute it with a bounded timeout and a sanitized environment.
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
for candidate in (PROJECT_ROOT, SCRIPTS_DIR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from scripts.convert_sigma import convert_rule, load_config  # noqa: E402
from scripts.kql._facade_impl import convert_kql_to_logan, load_mapping_config  # noqa: E402
from scripts.ql import elastic as elastic_converter  # noqa: E402


LANGUAGES = {
    "sigma_yaml",
    "sentinel_kql",
    "splunk_spl",
    "elastic_lucene",
    "elastic_kuery",
    "elastic_eql",
    "elastic_esql",
    "elastic_toml",
    "osquery_sql",
    "yara",
    "oci_logan",
}
MAX_QUERY_CHARS = 20_000
UNSAFE_YAML_MARKERS = ("!!python", "!!binary", "!!omap", "!!set", "!!pairs")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def response(
    *,
    source_language: str,
    source_query: str,
    logan_query: str,
    support_level: str,
    explanation: str,
    warnings: list[dict[str, str]] | None = None,
    metadata: dict[str, Any] | None = None,
    backend: str = "scripts/logan_workbench_convert.py",
) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "generated_at": now_iso(),
        "source_language": source_language,
        "source_query": source_query,
        "logan_query": logan_query,
        "support_level": support_level,
        "explanation": explanation,
        "warnings": warnings or [],
        "metadata": metadata or {},
        "backend": backend,
    }


def warning(code: str, message: str, severity: str = "warning") -> dict[str, str]:
    return {"code": code, "message": message, "severity": severity}


def normalize_input(raw: bytes) -> dict[str, Any]:
    if len(raw) > MAX_QUERY_CHARS + 4096:
        raise ValueError("request too large")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON request: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise ValueError("request body must be an object")
    language = payload.get("source_language")
    query = payload.get("source_query")
    if language not in LANGUAGES:
        raise ValueError("unsupported source_language")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("source_query is required")
    if len(query) > MAX_QUERY_CHARS:
        raise ValueError(f"source_query exceeds {MAX_QUERY_CHARS} characters")
    return {"source_language": language, "source_query": query}


def convert_sigma_yaml(query: str) -> dict[str, Any]:
    lowered = query.lower()
    unsafe = [marker for marker in UNSAFE_YAML_MARKERS if marker in lowered]
    if unsafe:
        return response(
            source_language="sigma_yaml",
            source_query=query,
            logan_query="",
            support_level="unsupported",
            explanation="The Sigma input contains YAML tags that are not accepted by the workbench backend.",
            warnings=[warning("unsafe_yaml_tag", f"Blocked YAML tag marker: {marker}", "error") for marker in unsafe],
        )

    field_map, logsource_map = load_config()
    with tempfile.TemporaryDirectory(prefix="logan-forge-sigma-") as tmp:
        rule_path = Path(tmp) / "rule.yml"
        rule_path.write_text(query)
        converted = convert_rule(str(rule_path), field_map, logsource_map)

    if not converted:
        return response(
            source_language="sigma_yaml",
            source_query=query,
            logan_query="",
            support_level="unsupported",
            explanation="The Sigma rule could not be parsed into a detection with a valid condition.",
            warnings=[warning("sigma_parse_failed", "The rule must contain a detection block and condition.", "error")],
        )

    warnings: list[dict[str, str]] = []
    if converted.get("logsource_fallback"):
        warnings.append(warning("logsource_fallback", "No exact Sigma logsource mapping was found; OCI Audit Logs was used."))
    if converted.get("requires_aggregation"):
        warnings.append(
            warning(
                "aggregation_condition",
                "Sigma aggregation/timeframe semantics were reduced to a base Logan filter. Validate before deploying.",
            )
        )

    return response(
        source_language="sigma_yaml",
        source_query=query,
        logan_query=converted.get("query", ""),
        support_level="partial" if warnings else "supported",
        explanation="Converted through scripts/convert_sigma.py using the repository Sigma field and logsource mappings.",
        warnings=warnings,
        metadata={
            "title": converted.get("title", ""),
            "sigma_id": converted.get("sigma_id", ""),
            "level": converted.get("level", ""),
            "mitre_attack": converted.get("mitre_attack", {}),
            "stig_ids": converted.get("stig_ids", []),
            "logsource": converted.get("logsource", {}),
        },
    )


def convert_sentinel_kql(query: str) -> dict[str, Any]:
    logan_query, source_info, errors = convert_kql_to_logan(query, load_mapping_config())
    if errors:
        return response(
            source_language="sentinel_kql",
            source_query=query,
            logan_query="",
            support_level="unsupported",
            explanation="The Sentinel KQL converter blocked unsupported or lossy semantics.",
            warnings=[warning("kql_conversion_error", item, "error") for item in errors],
        )
    return response(
        source_language="sentinel_kql",
        source_query=query,
        logan_query=logan_query,
        support_level="supported",
        explanation="Converted through the repository Sentinel-to-OCI KQL conversion pipeline and mapping shards.",
        metadata={"source_info": source_info},
    )


def convert_splunk_spl(query: str) -> dict[str, Any]:
    lowered = query.lower()
    warnings = [warning("heuristic_spl", "SPL conversion uses deterministic pattern mapping; validate advanced SPL manually.")]
    if "`" in query or "$" in query:
        warnings.append(warning("spl_macro", "SPL macro or token syntax was detected and ignored."))
    if " join " in lowered or " transaction " in lowered:
        return response(
            source_language="splunk_spl",
            source_query=query,
            logan_query="",
            support_level="unsupported",
            explanation="SPL joins and transactions require backend correlation logic and are not safely rewritten.",
            warnings=[warning("unsupported_join_or_transaction", "join/transaction semantics are blocked.", "error")],
        )

    source = "Windows Sysmon Events" if "sysmon" in lowered or "eventcode=1" in lowered else "SOC Application Logs"
    predicates = [f"'Log Source' = '{source}'"]
    if re.search(r"\beventcode\s*=\s*1\b", query, flags=re.IGNORECASE):
        predicates.append("'Event ID' = '1'")
    if "powershell.exe" in lowered:
        predicates.append("'Process Name' like '*\\\\powershell.exe'")
    if "encodedcommand" in lowered or " -enc " in lowered:
        predicates.append("('Command Line' like '* -enc *' or 'Command Line' like '* -EncodedCommand *')")
    if "src_ip" in lowered:
        source = "OCI VCN Flow Logs"
        predicates = [f"'Log Source' = '{source}'"]

    logan = " and ".join(predicates)
    if "lookup" in lowered:
        logan += " | lookup threat_ips 'Source IP'"
        warnings.append(warning("lossy_lookup", "Ensure an OCI lookup table named threat_ips exists before using this query."))
    if "| stats" in lowered:
        if "src_ip" in lowered:
            logan += " | stats count as count by 'Source IP'"
        else:
            logan += " | stats count as count by 'Host Name', 'User Name', 'Command Line'"
    if "sort -" in lowered:
        logan += " | sort -count"
    logan += " | head 100" if "| head" not in lowered else ""

    return response(
        source_language="splunk_spl",
        source_query=query,
        logan_query=logan,
        support_level="lossy" if any(item["code"] == "lossy_lookup" for item in warnings) else "partial",
        explanation="Mapped common SPL search, stats, lookup, and sort constructs into Logan QL patterns.",
        warnings=warnings,
    )



def convert_oci_logan(query: str) -> dict[str, Any]:
    kql_markers = (" summarize ", " project ", " extend ", " == ", " has ")
    warnings = []
    if any(marker in f" {query.lower()} " for marker in kql_markers):
        warnings.append(warning("mixed_query_language", "Input looks like KQL, not OCI Logan QL. Choose Sentinel KQL for conversion."))
    return response(
        source_language="oci_logan",
        source_query=query,
        logan_query=query.strip(),
        support_level="supported" if not warnings else "partial",
        explanation="OCI Logan QL input is passed through after bounded validation.",
        warnings=warnings,
    )


def main() -> int:
    try:
        payload = normalize_input(sys.stdin.buffer.read())
        language = payload["source_language"]
        query = payload["source_query"]
        if language == "sigma_yaml":
            out = convert_sigma_yaml(query)
        elif language == "sentinel_kql":
            out = convert_sentinel_kql(query)
        elif language == "splunk_spl":
            out = convert_splunk_spl(query)
        elif language in {"elastic_lucene", "elastic_kuery"}:
            out = elastic_converter.convert_elastic(query, language)
        elif language == "elastic_eql":
            out = elastic_converter.convert_elastic_eql(query)
        elif language == "elastic_esql":
            out = elastic_converter.convert_elastic_esql(query)
        elif language == "elastic_toml":
            out = elastic_converter.convert_elastic_toml(query)
        elif language == "osquery_sql":
            out = elastic_converter.convert_osquery_sql(query)
        elif language == "yara":
            out = elastic_converter.convert_yara(query)
        else:
            out = convert_oci_logan(query)
        print(json.dumps(out, sort_keys=True))
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI boundary returns sanitized JSON.
        print(
            json.dumps(
                {
                    "schema_version": "1.0.0",
                    "generated_at": now_iso(),
                    "logan_query": "",
                    "support_level": "unsupported",
                    "explanation": "Conversion request was rejected by the backend boundary.",
                    "warnings": [warning("request_rejected", str(exc), "error")],
                    "metadata": {},
                    "backend": "scripts/logan_workbench_convert.py",
                },
                sort_keys=True,
            )
        )
        return 2


if __name__ == "__main__":
    os.chdir(PROJECT_ROOT)
    raise SystemExit(main())
