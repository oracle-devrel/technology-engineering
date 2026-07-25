#!/usr/bin/env python3
"""Runtime profile helpers for Microsoft Sentinel migration conversion."""

from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_PROFILE_NAME = "azure_as_is"
DEFAULT_PROFILE_DIR = PROJECT_DIR / "config" / "mapping" / "profiles"


def load_mapping_profile(profile: str | None, profile_dir: Path = DEFAULT_PROFILE_DIR) -> dict:
    """Load a Sentinel runtime mapping profile by name or path."""
    if not profile:
        return {}
    profile_path = Path(profile)
    if not profile_path.suffix:
        profile_path = profile_dir / f"{profile}.yaml"
    if not profile_path.exists():
        raise FileNotFoundError(f"mapping profile not found: {profile_path}")
    import yaml

    payload = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"mapping profile must be a YAML object: {profile_path}")
    payload.setdefault("name", profile_path.stem)
    return payload


def apply_mapping_profile(mapping: dict, profile: dict) -> dict:
    """Return a copy of mapping with profile table source overrides applied."""
    if not profile:
        return mapping
    profiled = copy.deepcopy(mapping)
    for table, override in (profile.get("table_source_overrides") or {}).items():
        if table not in profiled.get("tables", {}):
            continue
        if isinstance(override, dict):
            profiled["tables"][table] = {**profiled["tables"][table], **override}
    return profiled


def _load_discovery_evidence(discovery_report: Path | None) -> dict[str, dict]:
    if not discovery_report:
        return {}
    path = Path(discovery_report)
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        item.get("content_id", "") or item.get("source_path", ""): item
        for item in payload.get("items", [])
        if item.get("content_id") or item.get("source_path")
    }


def _candidate_evidence_score(item: dict) -> int:
    score = 0
    if item.get("enabled"):
        score += 1000
    score += min(sum(int(value or 0) for value in item.get("hit_counts_by_lookback", {}).values()), 500)
    score += min(int(item.get("stored_log_volume_bytes", 0) or 0) // 1_000_000, 250)
    if item.get("dashboard_references"):
        score += 200
    return score


def apply_discovery_evidence(candidates: list[dict], discovery_report: Path | None) -> list[dict]:
    """Annotate Sentinel candidates with discovery priority evidence."""
    evidence = _load_discovery_evidence(discovery_report)
    if not evidence:
        return candidates
    annotated = []
    for candidate in candidates:
        item = (
            evidence.get(candidate.get("sentinel_id", ""))
            or evidence.get(candidate.get("source_path", ""))
            or {}
        )
        if not item:
            annotated.append(candidate)
            continue
        annotated.append({
            **candidate,
            "discovery_evidence_score": _candidate_evidence_score(item),
            "discovery_hit_counts_by_lookback": item.get("hit_counts_by_lookback", {}),
            "discovery_stored_log_volume_bytes": item.get("stored_log_volume_bytes", 0),
            "discovery_dashboard_references": item.get("dashboard_references", []),
            "enabled": item.get("enabled", candidate.get("enabled", True)),
        })
    return annotated


def build_migration_plan_from_report(report: dict, output_path: Path) -> dict:
    """Write a priority-ordered migration plan from a conversion report."""
    items = []
    for attempted in report.get("attempted", []):
        blockers = []
        for reason in attempted.get("skip_reasons", []):
            blocker_type = "unsupported"
            if reason.startswith("unsupported Sentinel field mapping:"):
                blocker_type = "field_mapping"
            elif reason.startswith("unsupported Sentinel table:"):
                blocker_type = "table_mapping"
            elif "unsupported KQL" in reason or "unsupported function" in reason:
                blocker_type = "kql_support"
            elif reason == "live OCI validation failed":
                blocker_type = "live_validation"
            blockers.append({"type": blocker_type, "detail": reason})
        blockers.extend(
            {"type": "local_validation", "detail": reason}
            for reason in attempted.get("local_validation_errors", [])
        )
        if attempted.get("live_validation_status") == "failed":
            blockers.append({"type": "live_validation", "detail": "live OCI validation failed"})
        items.append({
            "content_id": attempted.get("sentinel_id", "") or attempted.get("source_path", ""),
            "title": attempted.get("title", ""),
            "kind": "analytics_rule",
            "priority_score": int(attempted.get("quality_score", 0) or 0),
            "enabled": True,
            "severity": "",
            "source_tables": [],
            "mapped_oci_sources": [],
            "migration_status": "promoted" if attempted.get("conversion_status") == "promoted" else "blocked",
            "blockers": blockers,
            "next_validation": (
                "live_validation"
                if attempted.get("conversion_status") == "converted_not_written"
                else "complete" if attempted.get("conversion_status") == "promoted"
                else blockers[0]["type"] if blockers else "local_validation"
            ),
        })
    items.sort(key=lambda item: (-item["priority_score"], item["title"], item["content_id"]))
    payload = {
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "migration_report": str(output_path),
        "runtime_profile": report.get("runtime_profile", {}),
        "summary": {
            "planned_count": len(items),
            "ready_for_local_validation_count": sum(1 for item in items if not item["blockers"]),
            "blocked_count": sum(1 for item in items if item["blockers"]),
        },
        "items": items,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload
