#!/usr/bin/env python3
"""Tests for Sentinel backlog prioritization."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from scripts.sentinel_backlog_prioritize import (  # noqa: E402
    build_priority,
    render_priority,
)
from scripts.release_checklist import _sentinel_backlog_advisory  # noqa: E402


def _candidate(sentinel_id: str, title: str, query: str, *, severity: str = "high") -> dict:
    return {
        "sentinel_id": sentinel_id,
        "title": title,
        "source_path": f"Detections/{sentinel_id}.yaml",
        "source_url": f"https://example.test/{sentinel_id}",
        "severity": severity,
        "kind": "analytics_rule",
        "query": query,
        "mitre_attack": {"tactics": ["execution"], "techniques": ["T1059"]},
    }


def test_priority_excludes_promoted_and_counts_unblock_chain() -> None:
    candidates = {
        "generated_at": "2026-05-17T00:00:00+00:00",
        "source": {"commit": "abc123"},
        "candidates": [
            _candidate("promoted", "Promoted", "SecurityEvent | where EventID == 1"),
            _candidate("one", "One", "SecurityEvent | where SubjectAccount == 'a'"),
            _candidate("two", "Two", "SecurityEvent | where SubjectAccount == 'b'"),
            _candidate("three", "Three", "SecurityEvent | summarize c=countif(EventID == 1)"),
        ],
    }
    report = {
        "attempted": [
            {
                "sentinel_id": "promoted",
                "conversion_status": "promoted",
                "output_file": "sentinel/promoted.json",
            }
        ]
    }

    priority = build_priority(
        candidates,
        report,
        mapping={"fields": {}, "tables": {"SecurityEvent": "SecurityEvent"}},
        sync={"mode": "test"},
    )

    ranked_ids = [row["sentinel_id"] for row in priority["ranked"]]
    assert "promoted" not in ranked_ids
    assert ranked_ids[:2] == ["one", "two"]
    assert priority["ranked"][0]["primary_blocker"] == "field_mapping:SubjectAccount"
    assert priority["ranked"][0]["phase9_trace"] == "MAP-05"
    assert priority["ranked"][0]["unblock_chain_length"] == 1


def test_supported_operator_shapes_are_not_static_blockers() -> None:
    candidates = {
        "generated_at": "2026-05-17T00:00:00+00:00",
        "source": {"commit": "abc123"},
        "candidates": [
            _candidate(
                "supported",
                "Supported",
                (
                    "SecurityEvent\n"
                    "| extend IsFailure = iff(EventID == 4625, 'yes', 'no'), "
                    "ActorLower = tolower(tostring(Account))\n"
                    "| summarize Failures=countif(EventID == 4625) by bin(TimeGenerated, 15m), Account\n"
                    "| top 5 by Failures desc"
                ),
            ),
        ],
    }

    priority = build_priority(
        candidates,
        {"attempted": []},
        mapping={"fields": {"Account": "User", "EventID": "'Event ID'"}, "tables": {"SecurityEvent": {}}},
        sync={"mode": "test"},
    )

    blockers = priority["ranked"][0]["all_blockers"]
    assert "operator:extend.iff" not in blockers
    assert "operator:extend.tostring" not in blockers
    assert "operator:extend.tolower" not in blockers
    assert "operator:countif" not in blockers
    assert "operator:bin" not in blockers
    assert "operator:top" not in blockers
    assert blockers == ["parser_readiness:unknown"]


def test_unsupported_kql_features_remain_static_blockers() -> None:
    candidates = {
        "generated_at": "2026-05-17T00:00:00+00:00",
        "source": {"commit": "abc123"},
        "candidates": [
            _candidate(
                "unsupported",
                "Unsupported",
                "SecurityEvent | join (SecurityEvent) on Account | mv-expand TargetResources",
            ),
        ],
    }

    priority = build_priority(
        candidates,
        {"attempted": []},
        mapping={"fields": {"Account": "User"}, "tables": {"SecurityEvent": {}}},
        sync={"mode": "test"},
    )

    blockers = priority["ranked"][0]["all_blockers"]
    assert "operator:join" in blockers
    assert "operator:mv-expand" in blockers


def test_externaldata_is_a_feed_dependency_not_operator_blocker() -> None:
    candidates = {
        "generated_at": "2026-05-17T00:00:00+00:00",
        "source": {"commit": "abc123"},
        "candidates": [
            _candidate(
                "feed",
                "Feed",
                (
                    "let iocs = externaldata(IoC:string, Type:string) "
                    "[@\"https://example.test/iocs.csv\"] with(format=\"csv\"); "
                    "CommonSecurityLog | where DestinationIP in (iocs)"
                ),
            ),
        ],
    }

    priority = build_priority(
        candidates,
        {"attempted": []},
        mapping={"fields": {"DestinationIP": "'Destination IP'"}, "tables": {"CommonSecurityLog": {}}},
        sync={"mode": "test"},
    )

    blockers = priority["ranked"][0]["all_blockers"]
    assert "feed_dependency:externaldata" in blockers
    assert "operator:externaldata" not in blockers


def test_priority_render_is_stable_json() -> None:
    candidates = {
        "generated_at": "2026-05-17T00:00:00+00:00",
        "source": {"commit": "abc123"},
        "candidates": [
            _candidate("one", "One", "SecurityEvent | where SubjectAccount == 'a'"),
        ],
    }
    priority = build_priority(candidates, {"attempted": []}, sync={"mode": "test"})

    rendered = render_priority(priority)

    assert json.loads(rendered)["summary"]["ranked_count"] == 1
    assert rendered == render_priority(priority)


def test_release_advisory_reads_priority_artifact(tmp_path: Path) -> None:
    priority_path = tmp_path / "sentinel_backlog_priority.json"
    priority_path.write_text(
        json.dumps({"summary": {"ranked_count": 2, "top_blocker": "operator:let"}}),
        encoding="utf-8",
    )

    advisory = _sentinel_backlog_advisory(priority_path)

    assert advisory["available"] is True
    assert advisory["text"] == "Sentinel backlog: 2 ranked; top blocker: operator:let"
