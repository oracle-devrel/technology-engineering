#!/usr/bin/env python3
"""Shared helpers for distinguishing saved-search query JSON from generated artifacts."""

from __future__ import annotations

from pathlib import Path

GENERATED_QUERY_ARTIFACT_FILENAMES = {
    "catalog.json",
    "content_candidates.json",
    "conversion_examples.json",
    "cross_ql_mapping_patterns.json",
    "dashboard_inventory.json",
    "detection_rule_specs.json",
    "log_source_field_dictionary.json",
    "logan_ql_reference_catalog.json",
    "manifest.json",
    "mapping_collisions.json",
    "migration_plan_sentinel.json",
    "octo_apm_workshop_bundle.json",
    "osquery_pack_bundle.json",
    "ql_conversion_capability_matrix.json",
    "siem_discovery_inventory.json",
    "sentinel_candidates.json",
    "sentinel_backlog_priority.json",
    "sentinel_conversion_report.json",
    "sentinel_feed_dependencies.json",
    "sentinel_synthetic_live_results.json",
    "sentinel_synthetic_plan.json",
}


def is_generated_query_artifact(path_or_name: str | Path) -> bool:
    """Return True when a JSON file is a generated inventory/metadata artifact."""
    return Path(path_or_name).name in GENERATED_QUERY_ARTIFACT_FILENAMES


def is_saved_search_query_file(path: str | Path) -> bool:
    """Return True for query JSON files that should contain a runnable OCL query."""
    query_path = Path(path)
    return query_path.suffix == ".json" and not is_generated_query_artifact(query_path)
