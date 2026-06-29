#!/usr/bin/env python3
"""Rank non-promoted Microsoft Sentinel candidates into actionable cohorts."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable

PROJECT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_DIR / "scripts"
DEFAULT_CANDIDATES_PATH = PROJECT_DIR / "queries" / "sentinel_candidates.json"
DEFAULT_REPORT_PATH = PROJECT_DIR / "queries" / "sentinel_conversion_report.json"
DEFAULT_OUTPUT_PATH = PROJECT_DIR / "queries" / "sentinel_backlog_priority.json"

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from scripts.kql._facade_impl import (  # noqa: E402
    classify_unsupported_kql,
    extract_source_tables,
    load_mapping_config,
)

MAP05_FIELDS = (
    "SubjectAccount",
    "SubjectDomainName",
    "SubjectLogonId",
    "SubjectUserSid",
    "SubjectUserName",
    "InitiatingProcessAccountDomain",
    "InitiatingProcessAccountName",
    "InitiatingProcessSHA256",
    "InitiatingProcessId",
    "MailboxOwnerUPN",
    "OfficeWorkload",
    "OrganizationName",
    "ClientInfoString",
    "UserType",
    "ParentProcessName",
    "ProcessId",
    "Exe",
    "LocalFile",
    "ActingProcessFileInternalName",
    "Logon_Type",
    "ObjectDN",
    "ObjectName",
    "AttributeLDAPDisplayName",
    "EventData",
)

UNSUPPORTED_REASON_BLOCKERS: tuple[tuple[str, str], ...] = (
    ("unsupported KQL operator: join", "operator:join"),
    ("unsupported KQL operator: make-series", "operator:make-series"),
    ("unsupported KQL operator: mv-expand/mv-apply", "operator:mv-expand"),
    ("unsupported KQL operator: evaluate", "operator:evaluate"),
    ("unsupported KQL operator: parse", "operator:parse"),
    ("unsupported KQL construct: let variables", "operator:let"),
    ("unsupported KQL construct: datatable", "operator:datatable"),
    ("unsupported KQL construct: externaldata", "feed_dependency:externaldata"),
    ("unsupported KQL construct: watchlists", "operator:watchlists"),
    ("unsupported KQL construct: custom function invocation", "operator:invoke"),
    ("unsupported KQL function: parse_command_line", "operator:parse_command_line"),
    ("unsupported KQL function: materialize", "operator:materialize"),
    ("unsupported KQL function: strlen", "operator:strlen"),
    ("unsupported KQL JSON bag expansion", "operator:json_bag_expansion"),
    ("unsupported KQL regex extraction", "operator:extract"),
    ("unsupported KQL regex predicate", "operator:matches_regex"),
    ("unsupported KQL JSON/index path", "operator:json_index_path"),
)

TIER_DIFFICULTY = {"tier_1": 1, "tier_2": 2, "tier_3": 3}
SEVERITY_WEIGHT = {
    "critical": 40,
    "high": 30,
    "medium": 20,
    "low": 10,
    "informational": 5,
    "info": 5,
}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _candidate_rows(payload: dict) -> list[dict]:
    rows = payload.get("candidates", payload)
    if not isinstance(rows, list):
        raise ValueError("candidate payload must contain a candidates list")
    return rows


def _promoted_ids(report: dict) -> set[str]:
    promoted = set()
    for item in report.get("attempted", []):
        if item.get("conversion_status") == "promoted" or item.get("output_file"):
            sentinel_id = item.get("sentinel_id")
            if sentinel_id:
                promoted.add(str(sentinel_id))
    return promoted


def _attempted_by_id(report: dict) -> dict[str, dict]:
    return {
        str(item.get("sentinel_id")): item
        for item in report.get("attempted", [])
        if item.get("sentinel_id")
    }


def _contains_field(query: str, field: str) -> bool:
    return bool(re.search(rf"(?<![A-Za-z0-9_]){re.escape(field)}(?![A-Za-z0-9_])", query))


def _map05_blockers(query: str, mapping: dict) -> list[str]:
    mapped = mapping.get("fields", {})
    return [
        f"field_mapping:{field}"
        for field in MAP05_FIELDS
        if field not in mapped and _contains_field(query, field)
    ]


def _operator_blockers(query: str) -> list[str]:
    blockers = []
    for reason in classify_unsupported_kql(query):
        blocker = next(
            (candidate for prefix, candidate in UNSUPPORTED_REASON_BLOCKERS if reason.startswith(prefix)),
            f"converter:{reason}",
        )
        blockers.append(blocker)
    return blockers


def _table_blockers(query: str, mapping: dict) -> list[str]:
    return [
        f"table_mapping:{table}"
        for table in extract_source_tables(query)
        if table not in mapping.get("tables", {})
    ]


def _report_blockers(attempted: dict | None) -> list[str]:
    if not attempted:
        return []
    blockers = []
    for reason in attempted.get("skip_reasons", []) + attempted.get("local_validation_errors", []):
        if reason.startswith("unsupported Sentinel field mapping:"):
            blockers.append(f"field_mapping:{reason.split(':', 1)[1].strip()}")
        elif reason.startswith("unsupported Sentinel table:"):
            blockers.append(f"table_mapping:{reason.split(':', 1)[1].strip()}")
        elif "live validation" in reason:
            blockers.append("live_validation:failed")
        else:
            blockers.append(f"converter:{reason}")
    if attempted.get("live_validation_status") == "failed":
        blockers.append("live_validation:failed")
    return blockers


def classify_blockers(candidate: dict, attempted: dict | None, mapping: dict) -> tuple[list[str], str]:
    """Return ordered blockers plus a tier estimate for a candidate."""

    query = candidate.get("query", "") or ""
    blockers = []
    blockers.extend(_map05_blockers(query, mapping))
    blockers.extend(_operator_blockers(query))
    blockers.extend(_table_blockers(query, mapping))
    blockers.extend(_report_blockers(attempted))
    if not blockers:
        blockers.append("parser_readiness:unknown")

    seen = set()
    ordered = []
    for blocker in blockers:
        if blocker not in seen:
            ordered.append(blocker)
            seen.add(blocker)

    if attempted and attempted.get("tier"):
        tier = str(attempted["tier"])
    elif any(blocker.startswith(("operator:", "field_mapping:")) for blocker in ordered):
        tier = "tier_2"
    else:
        tier = "tier_3"
    return ordered, tier


def _mitre_score(candidate: dict) -> int:
    mitre = candidate.get("mitre_attack") or {}
    tactics = mitre.get("tactics") or []
    techniques = mitre.get("techniques") or []
    severity = str(candidate.get("severity", "medium")).lower()
    return (
        SEVERITY_WEIGHT.get(severity, 20)
        + len(tactics) * 15
        + len(techniques) * 10
    )


def _phase9_trace(blocker: str) -> str:
    if blocker.startswith("field_mapping:") and blocker.split(":", 1)[1] in MAP05_FIELDS:
        return "MAP-05"
    if blocker.startswith(("operator:", "directive:set")):
        return "Phase 9 operator scope"
    return ""


def _ranking_score(candidate: dict, blockers: list[str], tier: str, chain_length: int) -> int:
    trace_bonus = 1000 if _phase9_trace(blockers[0]) else 0
    difficulty_penalty = TIER_DIFFICULTY.get(tier, 3) * 10
    return (_mitre_score(candidate) * 100) + trace_bonus + (chain_length * 5) - difficulty_penalty


def build_priority(
    candidates_payload: dict,
    report: dict,
    *,
    mapping: dict | None = None,
    limit: int | None = None,
    sync: dict | None = None,
) -> dict:
    """Build the deterministic priority report."""

    mapping = mapping or load_mapping_config()
    promoted = _promoted_ids(report)
    attempted = _attempted_by_id(report)
    rows = []
    for candidate in _candidate_rows(candidates_payload):
        sentinel_id = str(candidate.get("sentinel_id", ""))
        if not sentinel_id or sentinel_id in promoted:
            continue
        blockers, tier = classify_blockers(candidate, attempted.get(sentinel_id), mapping)
        rows.append(
            {
                "sentinel_id": sentinel_id,
                "title": candidate.get("title", ""),
                "source_path": candidate.get("source_path", ""),
                "source_url": candidate.get("source_url", ""),
                "severity": candidate.get("severity", ""),
                "kind": candidate.get("kind", ""),
                "mitre_attack": candidate.get("mitre_attack", {"tactics": [], "techniques": []}),
                "tier": tier,
                "primary_blocker": blockers[0],
                "phase9_trace": _phase9_trace(blockers[0]),
                "all_blockers": blockers,
            }
        )

    blocker_counts = Counter(row["primary_blocker"] for row in rows)
    for row in rows:
        chain_length = max(blocker_counts[row["primary_blocker"]] - 1, 0)
        row["unblock_chain_length"] = chain_length
        row["priority_score"] = _ranking_score(row, row["all_blockers"], row["tier"], chain_length)

    rows.sort(
        key=lambda row: (
            -int(bool(row["phase9_trace"])),
            -int(row["priority_score"]),
            TIER_DIFFICULTY.get(row["tier"], 3),
            row["primary_blocker"],
            row["title"],
            row["source_path"],
            row["sentinel_id"],
        )
    )
    ranked = rows if limit is None else rows[:limit]
    for index, row in enumerate(ranked, start=1):
        row["rank"] = index

    top_blocker = ranked[0]["primary_blocker"] if ranked else ""
    return {
        "version": "1.0",
        "generated_from": {
            "candidates": "queries/sentinel_candidates.json",
            "conversion_report": "queries/sentinel_conversion_report.json",
        },
        "source_sync": sync or {
            "mode": "unknown",
            "candidate_generated_at": candidates_payload.get("generated_at", ""),
            "commit": (candidates_payload.get("source") or {}).get("commit", ""),
        },
        "summary": {
            "ranked_count": len(ranked),
            "total_backlog_candidates": len(rows),
            "top_blocker": top_blocker,
            "blocker_counts": dict(sorted(blocker_counts.items())),
        },
        "ranked": ranked,
    }


def render_priority(report: dict) -> str:
    return json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def run_sync(candidates_path: Path, *, refresh: bool = False) -> dict:
    command = [
        sys.executable,
        str(SCRIPTS_DIR / "sync_sentinel_kql.py"),
        "--no-fetch",
        "--output",
        str(candidates_path),
    ]
    if refresh:
        command.remove("--no-fetch")
        command.insert(2, "--refresh")
    subprocess.run(command, cwd=PROJECT_DIR, check=True)
    payload = _load_json(candidates_path)
    return {
        "mode": "refresh" if refresh else "no_fetch",
        "command": command,
        "candidate_generated_at": payload.get("generated_at", ""),
        "commit": (payload.get("source") or {}).get("commit", ""),
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES_PATH)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--limit", type=int, default=0, help="Limit ranked entries; 0 writes all entries.")
    parser.add_argument("--check", action="store_true", help="Fail if output is stale.")
    parser.add_argument("--skip-sync", action="store_true", help="Do not run sync_sentinel_kql.py first.")
    parser.add_argument("--refresh", action="store_true", help="Fetch latest Sentinel repo before prioritizing.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    sync = None
    if not args.skip_sync:
        sync = run_sync(args.candidates, refresh=args.refresh)
    elif args.check and args.output.exists():
        try:
            sync = (_load_json(args.output).get("source_sync") or None)
        except (OSError, json.JSONDecodeError):
            sync = None

    candidates_payload = _load_json(args.candidates)
    report = _load_json(args.report)
    priority = build_priority(
        candidates_payload,
        report,
        limit=None if args.limit == 0 else args.limit,
        sync=sync,
    )
    rendered = render_priority(priority)
    if args.check:
        if not args.output.exists() or args.output.read_text(encoding="utf-8") != rendered:
            print(f"stale Sentinel backlog priority artifact: {args.output}")
            return 1
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(
        "Sentinel backlog: "
        f"{priority['summary']['ranked_count']} ranked; "
        f"top blocker: {priority['summary']['top_blocker']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
