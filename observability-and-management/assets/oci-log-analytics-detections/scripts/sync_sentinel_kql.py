#!/usr/bin/env python3
"""Fetch and normalize Microsoft Sentinel KQL content.

This script only reads the official Azure/Azure-Sentinel repository. The clone
is kept in an ignored local cache and the normalized candidate list is consumed
by ``convert_sentinel_kql.py``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import yaml

PROJECT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CACHE_DIR = PROJECT_DIR / ".sentinel" / "Azure-Sentinel"
DEFAULT_OUTPUT = PROJECT_DIR / "queries" / "sentinel_candidates.json"
SENTINEL_REPO_URL = "https://github.com/Azure/Azure-Sentinel.git"
SENTINEL_WEB_URL = "https://github.com/Azure/Azure-Sentinel"
SENTINEL_LICENSE_URL = "https://github.com/Azure/Azure-Sentinel/blob/master/LICENSE"
DEFAULT_REF = "master"

SPARSE_PATTERNS = [
    "Detections/**",
    "Hunting Queries/**",
    "Solutions/*/Analytic Rules/**",
    "Solutions/*/Analytics Rules/**",
    "Solutions/*/Hunting Queries/**",
]


def _run_git(args: list[str], cwd: Path | None = None) -> str:
    """Run git and return stdout."""
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def sync_sentinel_repo(cache_dir: Path = DEFAULT_CACHE_DIR, ref: str = DEFAULT_REF, refresh: bool = False) -> str:
    """Clone or update the official Sentinel repository and return the pinned commit."""
    cache_dir = Path(cache_dir)
    if not (cache_dir / ".git").exists():
        cache_dir.parent.mkdir(parents=True, exist_ok=True)
        _run_git([
            "clone",
            "--filter=blob:none",
            "--no-checkout",
            SENTINEL_REPO_URL,
            str(cache_dir),
        ])
        _run_git(["sparse-checkout", "init", "--no-cone"], cwd=cache_dir)
        _run_git(["sparse-checkout", "set", *SPARSE_PATTERNS], cwd=cache_dir)
    elif refresh:
        _run_git(["fetch", "--prune", "origin"], cwd=cache_dir)

    _run_git(["checkout", ref], cwd=cache_dir)
    return _run_git(["rev-parse", "HEAD"], cwd=cache_dir)


def resolve_sentinel_commit(repo_dir: Path = DEFAULT_CACHE_DIR) -> str:
    """Return the checked-out Sentinel commit, if available."""
    try:
        return _run_git(["rev-parse", "HEAD"], cwd=Path(repo_dir))
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def iter_sentinel_yaml_files(repo_dir: Path) -> Iterable[Path]:
    """Yield Sentinel Analytics Rules and Hunting Queries YAML files."""
    repo_dir = Path(repo_dir)
    candidates: set[Path] = set()
    include_markers = (
        "Detections",
        "Hunting Queries",
        "Analytic Rules",
        "Analytics Rules",
    )
    for path in repo_dir.rglob("*.y*ml"):
        rel_parts = path.relative_to(repo_dir).parts
        if any(marker in rel_parts for marker in include_markers):
            candidates.add(path)
    yield from sorted(candidates)


def _normalize_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _normalize_tactic(value: str) -> str:
    text = str(value).strip()
    if not text:
        return ""
    out = []
    previous_lower = False
    for char in text:
        if char.isupper() and previous_lower:
            out.append("_")
        elif char in (" ", "-", "."):
            out.append("_")
            previous_lower = False
            continue
        out.append(char.lower())
        previous_lower = char.islower() or char.isdigit()
    return "".join(out).strip("_")


def _normalize_connectors(connectors) -> list[dict]:
    normalized = []
    for connector in _normalize_list(connectors):
        if not isinstance(connector, dict):
            continue
        data_types = connector.get("dataTypes", connector.get("data_types", []))
        normalized.append({
            "connector_id": connector.get("connectorId", connector.get("connector_id", "")),
            "data_types": [str(item) for item in _normalize_list(data_types)],
        })
    return normalized


def _detect_kind(path: Path, payload: dict) -> str:
    parts = set(path.parts)
    if "Hunting Queries" in parts or str(payload.get("kind", "")).lower() == "hunting":
        return "hunting_query"
    return "analytics_rule"


def _stable_sentinel_id(source_path: str, title: str) -> str:
    digest = hashlib.sha256(f"{source_path}\0{title}".encode("utf-8")).hexdigest()[:16]
    return f"sentinel-{digest}"


def normalize_sentinel_rule(path: Path, payload: dict, repo_root: Path | None = None, commit: str = "") -> dict:
    """Normalize one Sentinel YAML payload into the converter candidate shape."""
    repo_root = Path(".") if repo_root is None else Path(repo_root)
    source_path = Path(path)
    try:
        rel_path = source_path.relative_to(repo_root).as_posix()
    except ValueError:
        rel_path = source_path.as_posix()

    title = str(payload.get("name") or payload.get("displayName") or payload.get("title") or source_path.stem)
    sentinel_id = str(payload.get("id") or _stable_sentinel_id(rel_path, title))
    severity = str(payload.get("severity") or payload.get("level") or "medium").lower()
    tactics = [_normalize_tactic(tactic) for tactic in _normalize_list(payload.get("tactics"))]
    tactics = [tactic for tactic in tactics if tactic]
    techniques = [str(item) for item in _normalize_list(
        payload.get("relevantTechniques", payload.get("techniques", []))
    )]
    source_ref = commit or DEFAULT_REF

    return {
        "sentinel_id": sentinel_id,
        "title": title,
        "description": str(payload.get("description") or ""),
        "severity": severity,
        "kind": _detect_kind(Path(rel_path), payload),
        "query": str(payload.get("query") or ""),
        "required_data_connectors": _normalize_connectors(payload.get("requiredDataConnectors", [])),
        "mitre_attack": {
            "tactics": tactics,
            "techniques": techniques,
        },
        "entity_mappings": payload.get("entityMappings", []),
        "query_frequency": payload.get("queryFrequency", ""),
        "query_period": payload.get("queryPeriod", ""),
        "trigger_operator": payload.get("triggerOperator", ""),
        "trigger_threshold": payload.get("triggerThreshold", ""),
        "source_path": rel_path,
        "source_url": f"{SENTINEL_WEB_URL}/blob/{source_ref}/{rel_path}",
        "source_repository": SENTINEL_WEB_URL,
        "attribution": {
            "source": "Microsoft Sentinel",
            "repository": "Azure/Azure-Sentinel",
            "license": "MIT",
            "license_url": SENTINEL_LICENSE_URL,
        },
    }


def load_sentinel_candidates(repo_dir: Path = DEFAULT_CACHE_DIR, commit: str = "") -> list[dict]:
    """Load and normalize all Sentinel YAML rules from a local checkout."""
    candidates = []
    repo_dir = Path(repo_dir)
    for path in iter_sentinel_yaml_files(repo_dir):
        try:
            with path.open(encoding="utf-8") as handle:
                payload = yaml.safe_load(handle) or {}
        except (OSError, yaml.YAMLError):
            continue
        if not isinstance(payload, dict) or not payload.get("query"):
            continue
        candidates.append(normalize_sentinel_rule(path, payload, repo_root=repo_dir, commit=commit))
    return candidates


def build_candidate_export(candidates: list[dict], commit: str) -> dict:
    """Build the normalized candidate export artifact."""
    return {
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "name": "Microsoft Sentinel",
            "repository": SENTINEL_WEB_URL,
            "commit": commit,
            "license": "MIT",
            "license_url": SENTINEL_LICENSE_URL,
        },
        "total_candidates": len(candidates),
        "candidates": candidates,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync official Microsoft Sentinel KQL content")
    parser.add_argument("--cache-dir", default=str(DEFAULT_CACHE_DIR), help="Ignored local Sentinel repo cache")
    parser.add_argument("--ref", default=DEFAULT_REF, help="Git ref to checkout, default: master")
    parser.add_argument("--refresh", action="store_true", help="Fetch the latest remote changes before checkout")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Normalized candidate JSON output")
    parser.add_argument("--no-fetch", action="store_true", help="Use an existing checkout without git network calls")
    args = parser.parse_args()

    cache_dir = Path(args.cache_dir)
    if args.no_fetch:
        commit = resolve_sentinel_commit(cache_dir)
    else:
        commit = sync_sentinel_repo(cache_dir=cache_dir, ref=args.ref, refresh=args.refresh)

    candidates = load_sentinel_candidates(cache_dir, commit=commit)
    output = build_candidate_export(candidates, commit=commit)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")

    print(f"Sentinel repo: {cache_dir}")
    print(f"Commit: {commit or 'unknown'}")
    print(f"Candidates: {len(candidates)}")
    print(f"Output: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
