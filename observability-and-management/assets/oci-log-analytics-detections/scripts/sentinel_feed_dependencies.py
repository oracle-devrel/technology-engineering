#!/usr/bin/env python3
"""Build a deduplicated bundle of Sentinel external feed dependencies."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_INVENTORY = PROJECT_DIR / "queries" / "siem_discovery_inventory.json"
DEFAULT_OUTPUT = PROJECT_DIR / "queries" / "sentinel_feed_dependencies.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _canonical_dependency_key(dependency: dict[str, Any]) -> str:
    canonical = {
        "url": dependency.get("url", ""),
        "format": dependency.get("format", "csv"),
        "columns": dependency.get("columns", []),
        "options": dependency.get("options", {}),
    }
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"))


def _feed_id(dependency: dict[str, Any]) -> str:
    digest = hashlib.sha256(_canonical_dependency_key(dependency).encode("utf-8")).hexdigest()[:12]
    return f"feed_{digest}"


def _target_source(dependency: dict[str, Any]) -> str:
    candidates = dependency.get("staging", {}).get("source_candidates", [])
    if candidates:
        return str(candidates[0])
    return "Azure Log Analytics Custom Logs"


def _normalized_event_fields(dependency: dict[str, Any]) -> list[str]:
    fields = []
    for column in dependency.get("columns", []):
        name = column.get("name")
        if name and name not in fields:
            fields.append(str(name))
    return fields


def build_feed_bundle(inventory: dict[str, Any]) -> dict[str, Any]:
    """Build a deterministic external-feed staging bundle from discovery inventory."""

    feeds: dict[str, dict[str, Any]] = {}
    feed_refs: dict[str, set[str]] = {}
    for item in inventory.get("items", []):
        for dependency in item.get("feed_dependencies", []):
            if dependency.get("kind") != "externaldata":
                continue
            feed_id = _feed_id(dependency)
            if feed_id not in feeds:
                feeds[feed_id] = {
                    "feed_id": feed_id,
                    "kind": "externaldata",
                    "names": [],
                    "url": dependency.get("url", ""),
                    "format": dependency.get("format", "csv"),
                    "columns": dependency.get("columns", []),
                    "options": dependency.get("options", {}),
                    "target_log_source": _target_source(dependency),
                    "staging_contract": {
                        "target": "oci_lookup_or_custom_log",
                        "normalized_event_fields": _normalized_event_fields(dependency),
                        "refresh_mode": "offline_or_scheduled_download",
                        "validation": [
                            "download feed out-of-band",
                            "normalize rows to JSONL with the listed fields",
                            "ingest into the target Log Analytics source",
                            "run live-hit validation for linked detections",
                        ],
                    },
                    "linked_content": [],
                }
                feed_refs[feed_id] = set()
            name = dependency.get("name")
            if name and name not in feeds[feed_id]["names"]:
                feeds[feed_id]["names"].append(name)
            ref_key = str(item.get("content_id", "")) + "\x00" + str(item.get("source_path", ""))
            if ref_key not in feed_refs[feed_id]:
                feeds[feed_id]["linked_content"].append({
                    "content_id": item.get("content_id", ""),
                    "title": item.get("title", ""),
                    "source_path": item.get("source_path", ""),
                })
                feed_refs[feed_id].add(ref_key)

    feed_list = sorted(feeds.values(), key=lambda feed: (feed["url"], feed["feed_id"]))
    candidate_ids = {
        ref["content_id"]
        for feed in feed_list
        for ref in feed["linked_content"]
        if ref.get("content_id")
    }
    return {
        "version": "1.0",
        "generated_at": utc_now(),
        "source_inventory": "queries/siem_discovery_inventory.json",
        "summary": {
            "feed_count": len(feed_list),
            "candidate_count": len(candidate_ids),
            "formats": dict(sorted({
                feed["format"]: sum(1 for item in feed_list if item["format"] == feed["format"])
                for feed in feed_list
            }.items())),
        },
        "feeds": feed_list,
    }


def validate_feed_bundle(bundle: dict[str, Any]) -> list[str]:
    errors = []
    if bundle.get("version") != "1.0":
        errors.append("$: version must be 1.0")
    if not isinstance(bundle.get("summary"), dict):
        errors.append("$: missing summary")
    feeds = bundle.get("feeds")
    if not isinstance(feeds, list):
        return errors + ["$: feeds must be an array"]
    seen_ids = set()
    for index, feed in enumerate(feeds):
        prefix = f"$.feeds[{index}]"
        feed_id = feed.get("feed_id")
        if not feed_id:
            errors.append(f"{prefix}: missing feed_id")
        elif feed_id in seen_ids:
            errors.append(f"{prefix}: duplicate feed_id {feed_id}")
        else:
            seen_ids.add(feed_id)
        if not feed.get("url"):
            errors.append(f"{prefix}: missing url")
        if not feed.get("target_log_source"):
            errors.append(f"{prefix}: missing target_log_source")
        if not isinstance(feed.get("linked_content"), list) or not feed.get("linked_content"):
            errors.append(f"{prefix}: missing linked_content")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true", help="Fail if the existing output is stale")
    args = parser.parse_args(argv)

    bundle = build_feed_bundle(_read_json(args.inventory))
    errors = validate_feed_bundle(bundle)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    if args.check:
        if not args.out.exists():
            print(f"{args.out} does not exist", file=sys.stderr)
            return 1
        existing = _read_json(args.out)
        existing_without_time = {**existing, "generated_at": bundle["generated_at"]}
        if existing_without_time != bundle:
            print(f"{args.out} is stale", file=sys.stderr)
            return 1
        print(f"OK - {args.out} is current")
        return 0

    _write_json(args.out, bundle)
    print(f"Wrote {bundle['summary']['feed_count']} feed dependencies to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
