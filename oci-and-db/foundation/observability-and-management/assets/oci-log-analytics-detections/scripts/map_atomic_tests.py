#!/usr/bin/env python3
"""
Map Atomic Red Team (ART) tests to detection rule queries.

Downloads the ART test index CSV from GitHub, matches tests to queries by
MITRE ATT&CK technique ID, and enriches query JSON files with an
atomic_red_team field for validation coverage tracking.

Usage:
  python3 scripts/map_atomic_tests.py --download --enrich --report --stats
  python3 scripts/map_atomic_tests.py --validate          # CI check
  python3 scripts/map_atomic_tests.py --dry-run --enrich   # Preview changes
"""

import argparse
import csv
import io
import json
import os
import sys
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from query_artifacts import is_saved_search_query_file  # noqa: E402

PROJECT_DIR = Path(__file__).parent.parent
QUERIES_DIR = PROJECT_DIR / "queries"
CONFIG_DIR = PROJECT_DIR / "config"
DOCS_DIR = PROJECT_DIR / "docs"
ART_INDEX_PATH = CONFIG_DIR / "art_index.csv"

ART_INDEX_URL = (
    "https://raw.githubusercontent.com/redcanaryco/atomic-red-team/"
    "master/atomics/Indexes/Indexes-CSV/index.csv"
)

# Maximum age before re-downloading (7 days)
CACHE_MAX_AGE_SECONDS = 7 * 24 * 3600

# Platforms that should have ART mappings (OCI is cloud-only, skip it)
TESTABLE_PLATFORMS = {"windows", "linux"}

TACTIC_DISPLAY = {
    "initial_access": "Initial Access",
    "execution": "Execution",
    "persistence": "Persistence",
    "privilege_escalation": "Privilege Escalation",
    "defense_evasion": "Defense Evasion",
    "credential_access": "Credential Access",
    "discovery": "Discovery",
    "lateral_movement": "Lateral Movement",
    "collection": "Collection",
    "command_and_control": "Command & Control",
    "exfiltration": "Exfiltration",
    "impact": "Impact",
}


# ─── Download & Parse ────────────────────────────────────────────


def download_art_index(force=False):
    """Download the ART CSV index from GitHub. Skip if cached < 7 days."""
    if not force and ART_INDEX_PATH.exists():
        age = time.time() - ART_INDEX_PATH.stat().st_mtime
        if age < CACHE_MAX_AGE_SECONDS:
            days = age / 86400
            print(f"  ART index cached ({days:.1f} days old), skipping download")
            return ART_INDEX_PATH

    print(f"  Downloading ART index from GitHub...")
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        req = urllib.request.Request(ART_INDEX_URL, headers={"User-Agent": "oci-detections/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        ART_INDEX_PATH.write_bytes(data)
        print(f"  Saved {len(data)} bytes to {ART_INDEX_PATH}")
    except Exception as e:
        print(f"  ERROR: Failed to download ART index: {e}", file=sys.stderr)
        if ART_INDEX_PATH.exists():
            print("  Using stale cached copy")
        else:
            sys.exit(1)
    return ART_INDEX_PATH


def parse_art_index(path=None):
    """Parse the ART CSV index into a dict keyed by technique ID.

    Returns:
        dict[str, list[dict]]: technique_id -> list of test dicts
    """
    path = path or ART_INDEX_PATH
    if not path.exists():
        print(f"  ERROR: ART index not found at {path}", file=sys.stderr)
        print("  Run with --download first")
        sys.exit(1)

    index = defaultdict(list)
    raw = path.read_text(encoding="utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(raw))

    for row in reader:
        # The CSV has columns: Tactic, Technique #, Technique Name,
        # Test #, Test Name, Test GUID, Executor Name, ...
        tech_id = row.get("Technique #", "").strip()
        if not tech_id:
            continue

        test = {
            "technique_id": tech_id,
            "tactic": row.get("Tactic", "").strip(),
            "technique_name": row.get("Technique Name", "").strip(),
            "test_number": row.get("Test #", "").strip(),
            "test_name": row.get("Test Name", "").strip(),
            "test_guid": row.get("Test GUID", "").strip(),
            "executor": row.get("Executor Name", "").strip(),
        }
        index[tech_id].append(test)

    print(f"  Parsed {sum(len(v) for v in index.values())} tests across {len(index)} techniques")
    return dict(index)


# ─── Matching ────────────────────────────────────────────────────


def match_technique(query_techniques, art_index):
    """Match query technique IDs to ART tests.

    Matching strategy:
      1. Exact match: T1059.001 -> T1059.001
      2. Parent fallback: T1059.001 -> T1059 (if no exact)
      3. Sub-technique expansion: T1059 -> T1059.001, T1059.002, etc.

    Returns:
        list[dict]: matched tests with match_type annotation
    """
    matched = []
    seen_guids = set()

    for tech_id in query_techniques:
        # 1. Exact match
        if tech_id in art_index:
            for test in art_index[tech_id]:
                if test["test_guid"] not in seen_guids:
                    seen_guids.add(test["test_guid"])
                    matched.append({**test, "match_type": "exact"})
            continue

        # 2. Parent fallback (T1059.001 -> T1059)
        if "." in tech_id:
            parent = tech_id.split(".")[0]
            if parent in art_index:
                for test in art_index[parent]:
                    if test["test_guid"] not in seen_guids:
                        seen_guids.add(test["test_guid"])
                        matched.append({**test, "match_type": "parent"})
                continue

        # 3. Sub-technique expansion (T1059 -> T1059.*)
        prefix = tech_id + "."
        for art_tech_id, tests in art_index.items():
            if art_tech_id.startswith(prefix):
                for test in tests:
                    if test["test_guid"] not in seen_guids:
                        seen_guids.add(test["test_guid"])
                        matched.append({**test, "match_type": "sub_technique"})

    return matched


def build_art_field(matches):
    """Build the atomic_red_team JSON field from matched tests."""
    techniques_with_tests = sorted(set(m["technique_id"] for m in matches))
    tests = []
    for m in matches:
        tech_id = m["technique_id"]
        tests.append({
            "technique_id": tech_id,
            "test_name": m["test_name"],
            "test_guid": m["test_guid"],
            "executor": m["executor"],
            "match_type": m["match_type"],
            "url": f"https://github.com/redcanaryco/atomic-red-team/blob/master/atomics/{tech_id}/{tech_id}.md",
        })

    return {
        "has_tests": len(tests) > 0,
        "test_count": len(tests),
        "techniques_with_tests": techniques_with_tests,
        "tests": tests,
    }


# ─── Enrich Queries ─────────────────────────────────────────────


def load_query(path):
    """Load a query JSON file."""
    with open(path) as f:
        return json.load(f)


def save_query(path, data):
    """Save a query JSON file with consistent formatting."""
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def iter_saved_query_files(queries_dir=None):
    """Yield top-level saved-search query JSON files from a query directory."""
    queries_dir = QUERIES_DIR if queries_dir is None else Path(queries_dir)
    for qfile in sorted(Path(queries_dir).glob("*.json")):
        if is_saved_search_query_file(qfile):
            yield qfile


def enrich_queries(art_index, dry_run=False, missing_only=False, queries_dir=None):
    """Add atomic_red_team field to each Windows/Linux query JSON."""
    stats = {"enriched": 0, "skipped_oci": 0, "no_match": 0, "already_has": 0}

    for qfile in iter_saved_query_files(queries_dir):
        query = load_query(qfile)
        platform = query.get("logsource", {}).get("product", "")

        if platform not in TESTABLE_PLATFORMS:
            stats["skipped_oci"] += 1
            continue

        if missing_only and "atomic_red_team" in query:
            stats["already_has"] += 1
            if dry_run:
                print(f"  [SKIP] {qfile.name}: already has atomic_red_team")
            continue

        techniques = query.get("mitre_attack", {}).get("techniques", [])
        if not techniques:
            # No techniques to match against
            art_field = build_art_field([])
            if dry_run:
                print(f"  [NO MATCH] {qfile.name}: 0 tests for []")
            if not dry_run:
                query["atomic_red_team"] = art_field
                save_query(qfile, query)
            stats["no_match"] += 1
            continue

        matches = match_technique(techniques, art_index)
        art_field = build_art_field(matches)

        if dry_run:
            status = "MATCH" if art_field["has_tests"] else "NO MATCH"
            print(f"  [{status}] {qfile.name}: {art_field['test_count']} tests "
                  f"for {techniques}")
        else:
            query["atomic_red_team"] = art_field
            save_query(qfile, query)

        if art_field["has_tests"]:
            stats["enriched"] += 1
        else:
            stats["no_match"] += 1

    return stats


# ─── Coverage Report ─────────────────────────────────────────────


def generate_coverage_report(art_index, queries_dir=None, docs_dir=None):
    """Generate docs/ART_COVERAGE_REPORT.md with coverage statistics."""
    docs_dir = DOCS_DIR if docs_dir is None else docs_dir
    docs_dir = Path(docs_dir)
    docs_dir.mkdir(parents=True, exist_ok=True)

    queries = []
    for qfile in iter_saved_query_files(queries_dir):
        queries.append(load_query(qfile))

    testable = [q for q in queries if q.get("logsource", {}).get("product") in TESTABLE_PLATFORMS]
    with_tests = [q for q in testable if q.get("atomic_red_team", {}).get("has_tests")]
    without_tests = [q for q in testable if not q.get("atomic_red_team", {}).get("has_tests")]

    total_test_count = sum(
        q.get("atomic_red_team", {}).get("test_count", 0) for q in testable
    )

    # Per-platform stats
    platform_stats = defaultdict(lambda: {"total": 0, "with_tests": 0, "test_count": 0})
    for q in testable:
        p = q.get("logsource", {}).get("product", "unknown")
        platform_stats[p]["total"] += 1
        art = q.get("atomic_red_team", {})
        if art.get("has_tests"):
            platform_stats[p]["with_tests"] += 1
        platform_stats[p]["test_count"] += art.get("test_count", 0)

    # Per-tactic stats
    tactic_stats = defaultdict(lambda: {"total": 0, "with_tests": 0})
    for q in testable:
        tactics = q.get("mitre_attack", {}).get("tactics", [])
        has = q.get("atomic_red_team", {}).get("has_tests", False)
        for t in tactics:
            tactic_stats[t]["total"] += 1
            if has:
                tactic_stats[t]["with_tests"] += 1

    # Unmapped techniques
    all_techniques = set()
    mapped_techniques = set()
    for q in testable:
        techs = q.get("mitre_attack", {}).get("techniques", [])
        all_techniques.update(techs)
        art = q.get("atomic_red_team", {})
        mapped_techniques.update(art.get("techniques_with_tests", []))

    unmapped = sorted(all_techniques - mapped_techniques)

    # Build report
    lines = []
    w = lines.append
    pct = (len(with_tests) / len(testable) * 100) if testable else 0

    w("# Atomic Red Team Coverage Report")
    w("")
    w(f"> **{len(with_tests)}/{len(testable)}** testable rules have ART tests "
      f"(**{pct:.0f}%** coverage) | {total_test_count} total test mappings")
    w("")

    # Summary table
    w("## Coverage by Platform")
    w("")
    w("| Platform | Rules | With Tests | Coverage | Total Tests |")
    w("|----------|-------|------------|----------|-------------|")
    for p in ["windows", "linux"]:
        s = platform_stats.get(p, {"total": 0, "with_tests": 0, "test_count": 0})
        p_pct = (s["with_tests"] / s["total"] * 100) if s["total"] else 0
        w(f"| {p.title()} | {s['total']} | {s['with_tests']} | {p_pct:.0f}% | {s['test_count']} |")
    w("")

    # Tactic breakdown
    w("## Coverage by MITRE Tactic")
    w("")
    w("| Tactic | Rules | With Tests | Coverage |")
    w("|--------|-------|------------|----------|")
    tactic_order = [
        "initial_access", "execution", "persistence", "privilege_escalation",
        "defense_evasion", "credential_access", "discovery", "lateral_movement",
        "collection", "command_and_control", "exfiltration", "impact",
    ]
    for t in tactic_order:
        if t not in tactic_stats:
            continue
        s = tactic_stats[t]
        t_pct = (s["with_tests"] / s["total"] * 100) if s["total"] else 0
        display = TACTIC_DISPLAY.get(t, t)
        w(f"| {display} | {s['total']} | {s['with_tests']} | {t_pct:.0f}% |")
    w("")

    # Unmapped techniques
    if unmapped:
        w("## Techniques Without ART Tests")
        w("")
        w(f"{len(unmapped)} techniques in our rules have no matching ART tests:")
        w("")
        for tech in unmapped:
            w(f"- `{tech}`")
        w("")

    # Rules without tests
    if without_tests:
        w("## Rules Without ART Tests")
        w("")
        w(f"{len(without_tests)} testable rules have no ART test mappings:")
        w("")
        w("| Rule | Platform | Techniques |")
        w("|------|----------|------------|")
        for q in without_tests:
            title = q["title"]
            plat = q.get("logsource", {}).get("product", "?")
            techs = ", ".join(q.get("mitre_attack", {}).get("techniques", []))
            w(f"| {title} | {plat} | {techs} |")
        w("")

    w("---")
    w("*Auto-generated by `scripts/map_atomic_tests.py`*")

    report_path = docs_dir / "ART_COVERAGE_REPORT.md"
    report_path.write_text("\n".join(lines))
    print(f"  Coverage report: {report_path}")
    return report_path


# ─── Validate ────────────────────────────────────────────────────


def validate_art_mapping(queries_dir=None):
    """CI check: ensure every non-OCI query has the atomic_red_team field.

    Returns exit code: 0 = pass, 1 = fail.
    """
    errors = 0
    checked = 0

    for qfile in iter_saved_query_files(queries_dir):
        query = load_query(qfile)
        platform = query.get("logsource", {}).get("product", "")

        if platform not in TESTABLE_PLATFORMS:
            continue

        checked += 1
        if "atomic_red_team" not in query:
            print(f"  MISSING: {qfile.name} has no atomic_red_team field")
            errors += 1
        else:
            art = query["atomic_red_team"]
            # Validate structure
            for key in ("has_tests", "test_count", "techniques_with_tests", "tests"):
                if key not in art:
                    print(f"  INVALID: {qfile.name} atomic_red_team missing '{key}'")
                    errors += 1

    if errors:
        print(f"\n  FAIL: {errors} issues in {checked} queries")
        return 1
    else:
        print(f"  PASS: {checked} queries have valid atomic_red_team fields")
        return 0


# ─── Stats ───────────────────────────────────────────────────────


def print_stats(queries_dir=None):
    """Print ART mapping statistics."""
    queries = []
    for qfile in iter_saved_query_files(queries_dir):
        queries.append(load_query(qfile))

    testable = [q for q in queries if q.get("logsource", {}).get("product") in TESTABLE_PLATFORMS]
    with_tests = [q for q in testable if q.get("atomic_red_team", {}).get("has_tests")]
    total_tests = sum(q.get("atomic_red_team", {}).get("test_count", 0) for q in testable)

    # Match type breakdown
    match_types = defaultdict(int)
    for q in testable:
        for t in q.get("atomic_red_team", {}).get("tests", []):
            match_types[t.get("match_type", "unknown")] += 1

    pct = (len(with_tests) / len(testable) * 100) if testable else 0

    print(f"\n  ART Coverage Statistics")
    print(f"  ─────────────────────────────────")
    print(f"  Total queries:      {len(queries)}")
    print(f"  Testable (non-OCI): {len(testable)}")
    print(f"  With ART tests:     {len(with_tests)} ({pct:.0f}%)")
    print(f"  Without ART tests:  {len(testable) - len(with_tests)}")
    print(f"  Total test matches: {total_tests}")
    print(f"")
    print(f"  Match types:")
    for mt in ["exact", "parent", "sub_technique"]:
        print(f"    {mt:15s}: {match_types.get(mt, 0)}")
    print(f"  ─────────────────────────────────")


# ─── CLI ─────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Map Atomic Red Team tests to detection queries"
    )
    parser.add_argument("--download", action="store_true",
                        help="Download ART index CSV from GitHub")
    parser.add_argument("--force", action="store_true",
                        help="Force re-download even if cached")
    parser.add_argument("--enrich", action="store_true",
                        help="Enrich query JSONs with ART mappings")
    parser.add_argument("--report", action="store_true",
                        help="Generate coverage report")
    parser.add_argument("--validate", action="store_true",
                        help="CI check: validate all queries have ART field")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview enrichment without writing files")
    parser.add_argument("--missing-only", action="store_true",
                        help="Only add atomic_red_team to queries missing the field")
    parser.add_argument("--stats", action="store_true",
                        help="Print ART mapping statistics")
    args = parser.parse_args()

    if not any([args.download, args.enrich, args.report, args.validate, args.stats]):
        parser.print_help()
        sys.exit(1)

    if args.download:
        download_art_index(force=args.force)

    if args.enrich:
        art_index = parse_art_index()
        stats = enrich_queries(
            art_index,
            dry_run=args.dry_run,
            missing_only=args.missing_only,
        )
        action = "Would enrich" if args.dry_run else "Enriched"
        print(f"\n  {action}: {stats['enriched']} queries with ART tests")
        print(f"  No match: {stats['no_match']} queries")
        print(f"  Skipped (OCI): {stats['skipped_oci']} queries")
        print(f"  Already had ART field: {stats['already_has']} queries")

    if args.report:
        if not any(QUERIES_DIR.glob("*.json")):
            print("  No queries found, skipping report")
        else:
            generate_coverage_report(parse_art_index() if not args.enrich else art_index)

    if args.stats:
        print_stats()

    if args.validate:
        sys.exit(validate_art_mapping())


if __name__ == "__main__":
    main()
