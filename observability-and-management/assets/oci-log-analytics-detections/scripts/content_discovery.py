#!/usr/bin/env python3
"""Build a normalized threat-intel and detection-candidate inventory.

The command is intentionally offline-first. It can consume local Sigma-style
rules and built-in Elastic/CSP coverage references without promoting anything
into production query surfaces.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from analyze_csp_gaps import ELASTIC_CSP_PATTERNS
from analyze_elastic_coverage import ELASTIC_WINDOWS_TECHNIQUES, load_our_techniques
from oci_config import PROJECT_DIR, QUERIES_DIR, SOURCE_CANDIDATE_GROUPS

SOURCE_REGISTRY_PATH = Path(PROJECT_DIR) / "config" / "threat_intel_sources.json"
OUTPUT_PATH = Path(QUERIES_DIR) / "content_candidates.json"
FIELD_DICTIONARY_PATH = Path(QUERIES_DIR) / "log_source_field_dictionary.json"

TACTIC_TAG_RE = re.compile(r"^attack\.([a-z_]+)$", re.IGNORECASE)
TECHNIQUE_TAG_RE = re.compile(r"^attack\.(t\d{4}(?:\.\d{3})?)$", re.IGNORECASE)

PLATFORM_LOG_SOURCES = {
    "windows": SOURCE_CANDIDATE_GROUPS.get("windows_sysmon", []),
    "linux": SOURCE_CANDIDATE_GROUPS.get("linux_syslog", []),
    "oci": SOURCE_CANDIDATE_GROUPS.get("oci_audit", []),
    "web": SOURCE_CANDIDATE_GROUPS.get("waf_security", []) + SOURCE_CANDIDATE_GROUPS.get("lb_access", []),
    "application": SOURCE_CANDIDATE_GROUPS.get("application_logs", []),
}

DEFAULT_LICENSE = {
    "status": "metadata_only",
    "notes": "Candidate metadata only; source detection logic must be reviewed before promotion.",
}


def _stable_id(parts: list[str]) -> str:
    value = "|".join(part for part in parts if part)
    return "cand_" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _normalize_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _dedupe_key(candidate: dict[str, Any]) -> str:
    sigma_id = candidate.get("sigma_id")
    if sigma_id:
        return f"sigma:{sigma_id}"
    core = [
        _normalize_title(candidate.get("title", "")),
        ",".join(sorted(candidate.get("mitre_techniques", []))),
        ",".join(sorted(candidate.get("candidate_log_sources", []))),
        ",".join(sorted(candidate.get("core_indicators", []))),
    ]
    return "content:" + hashlib.sha256("|".join(core).encode("utf-8")).hexdigest()[:24]


def _as_sorted_list(values: Any) -> list[str]:
    if not values:
        return []
    if isinstance(values, str):
        return [values]
    return sorted({str(value) for value in values if value not in (None, "")})


def _merge_list(existing: list[str], new_values: Any) -> list[str]:
    return sorted(set(existing) | set(_as_sorted_list(new_values)))


def _extract_mitre_from_tags(tags: list[str]) -> tuple[list[str], list[str]]:
    tactics: set[str] = set()
    techniques: set[str] = set()
    for tag in tags:
        tactic_match = TACTIC_TAG_RE.match(str(tag))
        if tactic_match and not tactic_match.group(1).startswith("t"):
            tactics.add(tactic_match.group(1).lower())
        technique_match = TECHNIQUE_TAG_RE.match(str(tag))
        if technique_match:
            techniques.add(technique_match.group(1).upper())
    return sorted(tactics), sorted(techniques)


def _strip_sigma_modifier(field_name: str) -> str:
    field = field_name.split("|", 1)[0]
    return field.strip()


def _extract_sigma_required_fields(value: Any) -> set[str]:
    fields: set[str] = set()
    if isinstance(value, dict):
        for key, nested in value.items():
            if key == "condition":
                continue
            if isinstance(nested, (dict, list)):
                fields.update(_extract_sigma_required_fields(nested))
            elif "|" in key or re.match(r"^[A-Za-z][A-Za-z0-9_. -]*$", key):
                fields.add(_strip_sigma_modifier(key))
    elif isinstance(value, list):
        for item in value:
            fields.update(_extract_sigma_required_fields(item))
    return {field for field in fields if field and not field.startswith("selection")}


def _extract_core_indicators(detection: dict[str, Any]) -> list[str]:
    indicators: set[str] = set()

    def visit(value: Any) -> None:
        if isinstance(value, str):
            if len(value) >= 4 and not value.lower().startswith("selection"):
                indicators.add(value.lower())
        elif isinstance(value, list):
            for item in value:
                visit(item)
        elif isinstance(value, dict):
            for item in value.values():
                visit(item)

    visit(detection)
    return sorted(indicators)[:20]


def _candidate_log_sources_for_logsource(logsource: dict[str, Any]) -> list[str]:
    product = str(logsource.get("product", "")).lower()
    category = str(logsource.get("category", "")).lower()
    service = str(logsource.get("service", "")).lower()
    if product == "windows" and service == "security":
        return SOURCE_CANDIDATE_GROUPS.get("windows_event_security", [])
    if product == "windows" and service == "system":
        return SOURCE_CANDIDATE_GROUPS.get("windows_event_system", [])
    if product == "windows" and category == "network_connection":
        return SOURCE_CANDIDATE_GROUPS.get("sysmon_network", [])
    if product == "linux" and service in {"auth", "secure"}:
        return SOURCE_CANDIDATE_GROUPS.get("linux_secure", [])
    if product in PLATFORM_LOG_SOURCES:
        return PLATFORM_LOG_SOURCES[product]
    return []


def normalize_sigma_rule(
    rule: dict[str, Any],
    *,
    local_reference: str = "",
    source_url: str = "",
    source_type: str = "sigmahq",
) -> dict[str, Any]:
    """Normalize a Sigma rule into the common candidate model."""
    tags = _as_sorted_list(rule.get("tags", []))
    tactics, techniques = _extract_mitre_from_tags(tags)
    logsource = rule.get("logsource", {}) or {}
    detection = rule.get("detection", {}) or {}
    required_fields = sorted(_extract_sigma_required_fields(detection))
    candidate_log_sources = _candidate_log_sources_for_logsource(logsource)
    platform = logsource.get("product") or logsource.get("service") or "unknown"

    title = rule.get("title", "Untitled Sigma Candidate")
    candidate = {
        "id": _stable_id([rule.get("id", ""), title, local_reference, source_url]),
        "title": title,
        "sigma_id": rule.get("id", ""),
        "source_url": source_url or (rule.get("references") or [""])[0],
        "local_reference": local_reference,
        "source_type": source_type,
        "source_types": [source_type],
        "affected_platform": str(platform).lower(),
        "mitre_tactics": tactics,
        "mitre_techniques": techniques,
        "candidate_log_sources": candidate_log_sources,
        "required_fields": required_fields,
        "detection_idea": rule.get("description") or f"Convert Sigma condition: {detection.get('condition', '')}",
        "core_indicators": _extract_core_indicators(detection),
        "confidence": rule.get("level", "medium"),
        "licensing": DEFAULT_LICENSE.copy(),
        "attribution": {"source": source_type, "references": _as_sorted_list(rule.get("references", []))},
        "review_status": "candidate",
    }
    candidate["dedupe_key"] = _dedupe_key(candidate)
    return candidate


def normalize_csp_pattern(tactic: str, pattern: dict[str, Any]) -> dict[str, Any]:
    """Normalize one Elastic CSP pattern into the candidate model."""
    has_oci_equivalent = bool(pattern.get("oci_equivalent"))
    title = f"OCI equivalent for {pattern['pattern']}" if has_oci_equivalent else pattern["pattern"]
    candidate = {
        "id": _stable_id(["elastic-csp", tactic, pattern["pattern"], pattern.get("oci_equivalent", "")]),
        "title": title,
        "sigma_id": "",
        "source_url": "https://github.com/elastic/detection-rules",
        "local_reference": "scripts/analyze_csp_gaps.py:ELASTIC_CSP_PATTERNS",
        "source_type": "elastic_csp_gap",
        "source_types": ["elastic_csp_gap"],
        "affected_platform": "oci" if has_oci_equivalent else "cloud",
        "mitre_tactics": [tactic],
        "mitre_techniques": _as_sorted_list(pattern.get("technique")),
        "candidate_log_sources": SOURCE_CANDIDATE_GROUPS.get("oci_audit", []) if has_oci_equivalent else [],
        "required_fields": ["eventType", "data.request.action"] if has_oci_equivalent else [],
        "detection_idea": (
            f"Detect OCI audit event {pattern['oci_equivalent']} for cloud pattern "
            f"{pattern['pattern']} observed in {pattern['csp']} references."
            if has_oci_equivalent else
            f"Research OCI telemetry equivalent for {pattern['pattern']} observed in {pattern['csp']} references."
        ),
        "core_indicators": _as_sorted_list(pattern.get("oci_equivalent")),
        "confidence": "medium" if has_oci_equivalent else "low",
        "licensing": DEFAULT_LICENSE.copy(),
        "attribution": {
            "source": "Elastic detection-rules technique coverage reference",
            "references": ["https://github.com/elastic/detection-rules"],
        },
        "review_status": "candidate",
    }
    candidate["dedupe_key"] = _dedupe_key(candidate)
    return candidate


def normalize_elastic_coverage_gap(tactic: str, technique: str, name: str) -> dict[str, Any]:
    """Create a candidate for a missing Elastic Windows technique reference."""
    title = f"Windows coverage gap: {technique} {name}"
    candidate = {
        "id": _stable_id(["elastic-windows", tactic, technique, name]),
        "title": title,
        "sigma_id": "",
        "source_url": "https://github.com/elastic/detection-rules",
        "local_reference": "scripts/analyze_elastic_coverage.py:ELASTIC_WINDOWS_TECHNIQUES",
        "source_type": "elastic_detection_reference",
        "source_types": ["elastic_detection_reference"],
        "affected_platform": "windows",
        "mitre_tactics": [tactic],
        "mitre_techniques": [technique],
        "candidate_log_sources": SOURCE_CANDIDATE_GROUPS.get("windows_sysmon", []),
        "required_fields": [],
        "detection_idea": f"Review Windows telemetry and create OCI Log Analytics detection coverage for {technique} {name}.",
        "core_indicators": [technique.lower()],
        "confidence": "medium",
        "licensing": DEFAULT_LICENSE.copy(),
        "attribution": {
            "source": "Elastic detection-rules technique coverage reference",
            "references": ["https://github.com/elastic/detection-rules"],
        },
        "review_status": "candidate",
    }
    candidate["dedupe_key"] = _dedupe_key(candidate)
    return candidate


def build_internal_workshop_candidates() -> list[dict[str, Any]]:
    """Return curated candidates for demo/workshop investigation workflows."""
    scenarios = [
        (
            "APM trace to Log Analytics threat hunting",
            "application",
            ["SOC Application Logs"],
            ["Trace ID", "Span ID", "Service Name", "Attack ID"],
            ["T1190", "T1557"],
        ),
        (
            "Identity compromise and OCI cloud abuse",
            "oci",
            SOURCE_CANDIDATE_GROUPS.get("oci_audit", []),
            ["eventType", "data.identity.principalName", "data.identity.ipAddress"],
            ["T1078", "T1098"],
        ),
        (
            "C2 and exfiltration across VCN and Network Firewall logs",
            "oci",
            SOURCE_CANDIDATE_GROUPS.get("vcn_flow", []) + SOURCE_CANDIDATE_GROUPS.get("network_firewall", []),
            ["Source IP", "Destination IP", "Bytes Sent", "Threat Name"],
            ["T1071", "T1041"],
        ),
    ]
    candidates = []
    for title, platform, sources, fields, techniques in scenarios:
        candidate = {
            "id": _stable_id(["internal-workshop", title]),
            "title": title,
            "sigma_id": "",
            "source_url": "",
            "local_reference": "curated workshop scenario",
            "source_type": "internal_workshop",
            "source_types": ["internal_workshop"],
            "affected_platform": platform,
            "mitre_tactics": [],
            "mitre_techniques": techniques,
            "candidate_log_sources": sources,
            "required_fields": fields,
            "detection_idea": f"Package dashboard-ready hunt workflow for {title}.",
            "core_indicators": [],
            "confidence": "high",
            "licensing": {"status": "owned", "notes": "Internal curated workflow."},
            "attribution": {"source": "internal curated workshop scenarios", "references": []},
            "review_status": "candidate",
        }
        candidate["dedupe_key"] = _dedupe_key(candidate)
        candidates.append(candidate)
    return candidates


def deduplicate_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Dedupe candidates by Sigma ID or normalized content fingerprint."""
    merged: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        candidate = {**candidate}
        key = candidate.get("dedupe_key") or _dedupe_key(candidate)
        candidate["dedupe_key"] = key
        if key not in merged:
            candidate.setdefault("source_types", _as_sorted_list(candidate.get("source_type")))
            candidate.setdefault("source_urls", _as_sorted_list(candidate.get("source_url")))
            candidate["duplicate_count"] = 1
            merged[key] = candidate
            continue

        existing = merged[key]
        existing["duplicate_count"] += 1
        existing["source_types"] = _merge_list(existing.get("source_types", []), candidate.get("source_type"))
        existing["source_urls"] = _merge_list(existing.get("source_urls", []), candidate.get("source_url"))
        for field in ("mitre_tactics", "mitre_techniques", "candidate_log_sources", "required_fields", "core_indicators"):
            existing[field] = _merge_list(existing.get(field, []), candidate.get(field, []))
        existing.setdefault("duplicates", []).append({
            "title": candidate.get("title", ""),
            "source_type": candidate.get("source_type", ""),
            "source_url": candidate.get("source_url", ""),
            "local_reference": candidate.get("local_reference", ""),
        })

    return sorted(merged.values(), key=lambda item: (item.get("classification", ""), item.get("title", "")))


def _field_names_from_dictionary(field_dictionary: dict[str, Any] | None) -> set[str]:
    if not field_dictionary:
        return set()
    return {field.get("display_name", "") for field in field_dictionary.get("fields", []) if field.get("display_name")}


def classify_candidate(candidate: dict[str, Any], field_dictionary: dict[str, Any] | None = None) -> dict[str, Any]:
    """Classify candidate readiness for OCI Log Analytics promotion."""
    field_names = _field_names_from_dictionary(field_dictionary)
    missing_fields = sorted(
        field for field in candidate.get("required_fields", [])
        if field_names and field not in field_names
    )
    reasons: list[str] = []

    if not candidate.get("candidate_log_sources"):
        classification = "not applicable to OCI Log Analytics"
        reasons.append("no candidate OCI Log Analytics source group is known")
    elif missing_fields:
        classification = "needs field mapping"
        reasons.append(f"missing field dictionary entries: {', '.join(missing_fields)}")
    elif candidate.get("source_type") == "internal_workshop":
        classification = "dashboard-only hunt"
        reasons.append("curated workflow candidate should be reviewed as dashboard/hunt content first")
    elif not candidate.get("required_fields"):
        classification = "needs field mapping"
        reasons.append("candidate does not declare required fields yet")
    else:
        classification = "ready to convert"
        reasons.append("candidate has source candidates and field requirements")

    return {
        **candidate,
        "classification": classification,
        "classification_reasons": reasons,
    }


def load_source_registry(path: Path = SOURCE_REGISTRY_PATH) -> dict[str, Any]:
    """Load the versioned threat-intel source registry."""
    if not path.exists():
        return {"version": "1.0", "sources": []}
    with path.open() as f:
        return json.load(f)


def load_field_dictionary(path: Path = FIELD_DICTIONARY_PATH) -> dict[str, Any] | None:
    """Load the generated field dictionary when available."""
    if not path.exists():
        return None
    with path.open() as f:
        return json.load(f)


def load_sigma_rules_from_dir(root: Path) -> list[dict[str, Any]]:
    """Load Sigma-style YAML rules from a local directory tree."""
    candidates = []
    for path in sorted(root.rglob("*.y*ml")):
        try:
            with path.open() as f:
                rule = yaml.safe_load(f)
        except (OSError, yaml.YAMLError):
            continue
        if not isinstance(rule, dict) or "detection" not in rule:
            continue
        candidates.append(normalize_sigma_rule(
            rule,
            local_reference=path.relative_to(PROJECT_DIR).as_posix()
            if path.is_relative_to(Path(PROJECT_DIR)) else str(path),
        ))
    return candidates


def build_candidate_inventory(
    *,
    include_builtin: bool = True,
    include_local_rules: bool = False,
    sigmahq_dir: Path | None = None,
    field_dictionary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the generated content candidate inventory."""
    candidates: list[dict[str, Any]] = []

    if include_builtin:
        for tactic, patterns in ELASTIC_CSP_PATTERNS.items():
            candidates.extend(normalize_csp_pattern(tactic, pattern) for pattern in patterns)

        our_techniques = load_our_techniques()
        for tactic, techniques in ELASTIC_WINDOWS_TECHNIQUES.items():
            for technique, name in techniques.items():
                if technique not in our_techniques:
                    candidates.append(normalize_elastic_coverage_gap(tactic, technique, name))

        candidates.extend(build_internal_workshop_candidates())

    if include_local_rules:
        candidates.extend(load_sigma_rules_from_dir(Path(PROJECT_DIR) / "rules"))

    if sigmahq_dir and sigmahq_dir.exists():
        candidates.extend(load_sigma_rules_from_dir(sigmahq_dir))

    deduped = deduplicate_candidates(candidates)
    classified = [classify_candidate(candidate, field_dictionary=field_dictionary) for candidate in deduped]
    status_counts = Counter(candidate["classification"] for candidate in classified)
    source_counts = Counter(
        source_type
        for candidate in classified
        for source_type in candidate.get("source_types", [candidate.get("source_type", "")])
        if source_type
    )

    return {
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_registry": load_source_registry(),
        "summary": {
            "total_candidates": len(classified),
            "by_classification": dict(sorted(status_counts.items())),
            "by_source_type": dict(sorted(source_counts.items())),
            "duplicates_collapsed": sum(candidate.get("duplicate_count", 1) - 1 for candidate in classified),
        },
        "candidates": classified,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate threat-intel detection candidate inventory")
    parser.add_argument("--out", default=str(OUTPUT_PATH), help="Output JSON path")
    parser.add_argument("--sigmahq-dir", help="Optional local SigmaHQ checkout to scan")
    parser.add_argument("--field-dictionary", default=str(FIELD_DICTIONARY_PATH),
                        help="Optional generated field dictionary used for readiness classification")
    parser.add_argument("--include-local-rules", action="store_true", help="Include repo-local source rules as candidates")
    parser.add_argument("--no-builtins", action="store_true", help="Skip built-in Elastic/CSP/workshop references")
    args = parser.parse_args()

    field_dictionary = load_field_dictionary(Path(args.field_dictionary)) if args.field_dictionary else None
    inventory = build_candidate_inventory(
        include_builtin=not args.no_builtins,
        include_local_rules=args.include_local_rules,
        sigmahq_dir=Path(args.sigmahq_dir) if args.sigmahq_dir else None,
        field_dictionary=field_dictionary,
    )
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {inventory['summary']['total_candidates']} content candidates to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
