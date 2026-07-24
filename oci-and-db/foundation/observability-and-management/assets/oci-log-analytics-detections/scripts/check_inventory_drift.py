#!/usr/bin/env python3
"""
check_inventory_drift.py — Fail-fast guard against README/STATUS counts drifting from queries/catalog.json.

Why: README.md and STATUS.md publish ~12 inventory numbers (source rules, generated queries,
Sentinel conversions, dashboards, MITRE/STIG coverage, etc.). These are hand-maintained today
and silently rot when scripts/generate_catalog.py regenerates the canonical inventory.

This tool extracts the published counts via regex, looks up the canonical value in
queries/catalog.json, and exits non-zero on any mismatch. Designed to run in CI and as a
pre-commit hook.

Usage:
    python3 scripts/check_inventory_drift.py            # check, exit 1 on drift
    python3 scripts/check_inventory_drift.py --report   # always exit 0, just print report
    python3 scripts/check_inventory_drift.py --json     # machine-readable output
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

REPO = Path(__file__).resolve().parent.parent
CATALOG = REPO / "queries" / "catalog.json"
DASHBOARD_INV = REPO / "queries" / "dashboard_inventory.json"
SENTINEL_REPORT = REPO / "queries" / "sentinel_conversion_report.json"
README = REPO / "README.md"
STATUS = REPO / "STATUS.md"


@dataclass
class DriftRule:
    """One reconciliation rule: regex to extract published count → canonical lookup.

    `canonical` receives the full sources dict: {"catalog", "dashboard", "sentinel"}.
    Most rules only need `s["catalog"]`; dashboard and sentinel rules pull from the
    other two generated artifacts.
    """
    label: str
    file: Path
    pattern: re.Pattern[str]
    canonical: Callable[[dict], object]
    notes: str = ""


def _inv(sources: dict, key: str) -> int:
    return int(sources["catalog"]["inventory"][key])


def _cat(sources: dict, key: str) -> int:
    return int(sources["catalog"][key])


def _dash(sources: dict, key: str) -> int:
    return int(sources["dashboard"]["summary"][key])


def _sent(sources: dict, key: str) -> int:
    return int(sources["sentinel"]["summary"][key])


# ─────────────────────────────────────────────────────────────────────────────
# Canonical reconciliation rules. Add a new rule when README/STATUS adds a count.
# Keep regex anchored so multi-line markdown does not over-match.
# ─────────────────────────────────────────────────────────────────────────────
DRIFT_RULES: list[DriftRule] = [
    DriftRule(
        label="source Sigma/YAML rules",
        file=README,
        pattern=re.compile(r"^- \*\*Source Sigma/YAML rules:\*\* (\d+)\s*$", re.M),
        canonical=lambda s: _inv(s, "source_yaml_rules"),
    ),
    DriftRule(
        label="Sigma-derived OCI query artifacts",
        file=README,
        pattern=re.compile(r"^- \*\*Sigma-derived OCI query artifacts:\*\* (\d+)\s*$", re.M),
        canonical=lambda s: _inv(s, "generated_sigma_queries"),
    ),
    DriftRule(
        label="top-level detections in queries/*.json",
        file=README,
        pattern=re.compile(r"(\d+) top-level detections in `queries/\*\.json`", re.M),
        canonical=lambda s: _inv(s, "generated_base_detection_queries"),
    ),
    DriftRule(
        label="browser/app telemetry detections",
        file=README,
        pattern=re.compile(r"(\d+) browser/app telemetry detections in `queries/apps/", re.M),
        canonical=lambda s: _inv(s, "source_derived_app_queries"),
    ),
    DriftRule(
        label="Microsoft Sentinel converted queries",
        file=README,
        pattern=re.compile(r"^- \*\*Microsoft Sentinel converted queries:\*\* (\d+) ", re.M),
        canonical=lambda s: _inv(s, "generated_sentinel_queries"),
    ),
    DriftRule(
        label="app telemetry analytics (curated)",
        file=README,
        pattern=re.compile(r"(\d+) app telemetry analytics in `queries/apps/`", re.M),
        canonical=lambda s: _inv(s, "curated_app_queries"),
    ),
    DriftRule(
        label="hunting analytics",
        file=README,
        pattern=re.compile(r"(\d+) hunting analytics in `queries/hunting/`", re.M),
        canonical=lambda s: _inv(s, "generated_hunting_queries"),
    ),
    DriftRule(
        label="total query artifacts/content items",
        file=README,
        pattern=re.compile(r"^- \*\*Total query artifacts/content items:\*\* ([\d,]+)\s*$", re.M),
        canonical=lambda s: _inv(s, "total_query_artifacts"),
        notes="strips commas before compare",
    ),
    DriftRule(
        label="MITRE techniques",
        file=README,
        pattern=re.compile(r"(\d+) techniques across \d+ tactics", re.M),
        canonical=lambda s: _inv(s, "combined_mitre_techniques"),
    ),
    DriftRule(
        label="MITRE tactics",
        file=README,
        pattern=re.compile(r"\d+ techniques across (\d+) tactics", re.M),
        canonical=lambda s: _inv(s, "combined_mitre_tactics"),
    ),
    DriftRule(
        label="STIG controls",
        file=README,
        pattern=re.compile(r"\d+ detections spanning (\d+) controls", re.M),
        canonical=lambda s: len(s["catalog"].get("stig_controls", [])),
        notes="catalog.stig_controls list length",
    ),
    # ── source-rule platform breakdown ──
    DriftRule(
        label="source rule breakdown: Windows",
        file=README,
        pattern=re.compile(r"Windows \((\d+)\)", re.M),
        canonical=lambda s: s["catalog"]["inventory"]["source_rule_breakdown"]["windows"],
    ),
    DriftRule(
        label="source rule breakdown: Cloud/OCI",
        file=README,
        pattern=re.compile(r"Cloud/OCI \((\d+)\)", re.M),
        canonical=lambda s: s["catalog"]["inventory"]["source_rule_breakdown"]["cloud"],
    ),
    DriftRule(
        label="source rule breakdown: Linux",
        file=README,
        pattern=re.compile(r"Linux \((\d+)\)", re.M),
        canonical=lambda s: s["catalog"]["inventory"]["source_rule_breakdown"]["linux"],
    ),
    DriftRule(
        label="source rule breakdown: Web/WAF",
        file=README,
        pattern=re.compile(r"Web/WAF \((\d+)\)", re.M),
        canonical=lambda s: s["catalog"]["inventory"]["source_rule_breakdown"]["web"],
    ),
    # ── Atomic Red Team coverage (canonical: catalog.art_coverage) ──
    DriftRule(
        label="ART coverage: rules with tests",
        file=README,
        pattern=re.compile(r"Atomic Red Team coverage:\*\* (\d+) / \d+ testable", re.M),
        canonical=lambda s: int(s["catalog"]["art_coverage"]["rules_with_tests"]),
    ),
    DriftRule(
        label="ART coverage: testable rules",
        file=README,
        pattern=re.compile(r"Atomic Red Team coverage:\*\* \d+ / (\d+) testable", re.M),
        canonical=lambda s: int(s["catalog"]["art_coverage"]["testable_rules"]),
    ),
    DriftRule(
        label="ART coverage: percent",
        file=README,
        pattern=re.compile(r"ART mappings \((\d+(?:\.\d+)?)%\)", re.M),
        canonical=lambda s: float(s["catalog"]["art_coverage"]["coverage_percent"]),
        notes="float compare — see check() for tolerance handling",
    ),
    DriftRule(
        label="STIG coverage: detections",
        file=README,
        pattern=re.compile(r"STIG coverage:\*\* (\d+) detections spanning", re.M),
        canonical=lambda s: sum(1 for r in s["catalog"].get("rules", []) if r.get("stig_ids")),
        notes="derived: count of rules with non-empty stig_ids",
    ),
    # ─────────────────────────────────────────────────────────────────────────
    # STATUS.md rules. Format differs slightly from README — patterns adjusted
    # per-line. Skipping prose discussion of historical activity (lines 89+)
    # which legitimately drifts as old facts age; only the structured summary
    # at the top is gated here.
    # ─────────────────────────────────────────────────────────────────────────
    DriftRule(
        label="STATUS: top-level detections in queries/",
        file=STATUS,
        pattern=re.compile(r"^\s+- (\d+) top-level detections in `queries/`", re.M),
        canonical=lambda s: _inv(s, "generated_base_detection_queries"),
    ),
    DriftRule(
        label="STATUS: browser/app telemetry detections",
        file=STATUS,
        pattern=re.compile(r"^\s+- (\d+) browser/app telemetry detections in `queries/apps/`", re.M),
        canonical=lambda s: _inv(s, "source_derived_app_queries"),
    ),
    DriftRule(
        label="STATUS: app telemetry analytics (curated)",
        file=STATUS,
        pattern=re.compile(r"^\s+- (\d+) app telemetry analytics\s*$", re.M),
        canonical=lambda s: _inv(s, "curated_app_queries"),
    ),
    DriftRule(
        label="STATUS: hunting analytics",
        file=STATUS,
        pattern=re.compile(r"^\s+- (\d+) hunting analytics\s*$", re.M),
        canonical=lambda s: _inv(s, "generated_hunting_queries"),
    ),
    DriftRule(
        label="STATUS: Microsoft Sentinel converted queries",
        file=STATUS,
        pattern=re.compile(r"Microsoft Sentinel converted queries: (\d+) live OCI parser-passing", re.M),
        canonical=lambda s: _inv(s, "generated_sentinel_queries"),
    ),
    DriftRule(
        label="STATUS: total content items (in saved-search line)",
        file=STATUS,
        pattern=re.compile(r"Saved searches: \d+ active dashboard saved searches; ([\d,]+) total content items", re.M),
        canonical=lambda s: _inv(s, "total_query_artifacts"),
    ),
    DriftRule(
        label="STATUS: MITRE techniques",
        file=STATUS,
        pattern=re.compile(r"MITRE ATT&CK coverage: (\d+) techniques / \d+ tactics", re.M),
        canonical=lambda s: _inv(s, "combined_mitre_techniques"),
    ),
    DriftRule(
        label="STATUS: MITRE tactics",
        file=STATUS,
        pattern=re.compile(r"MITRE ATT&CK coverage: \d+ techniques / (\d+) tactics", re.M),
        canonical=lambda s: _inv(s, "combined_mitre_tactics"),
    ),
    DriftRule(
        label="STATUS: STIG controls",
        file=STATUS,
        pattern=re.compile(r"STIG coverage: \d+ detections / (\d+) controls", re.M),
        canonical=lambda s: len(s["catalog"].get("stig_controls", [])),
    ),
    DriftRule(
        label="STATUS: STIG detections",
        file=STATUS,
        pattern=re.compile(r"STIG coverage: (\d+) detections / \d+ controls", re.M),
        canonical=lambda s: sum(1 for r in s["catalog"].get("rules", []) if r.get("stig_ids")),
    ),
    DriftRule(
        label="STATUS: ART rules with tests",
        file=STATUS,
        pattern=re.compile(r"Atomic Red Team coverage: (\d+) / \d+ testable", re.M),
        canonical=lambda s: int(s["catalog"]["art_coverage"]["rules_with_tests"]),
    ),
    DriftRule(
        label="STATUS: ART testable rules",
        file=STATUS,
        pattern=re.compile(r"Atomic Red Team coverage: \d+ / (\d+) testable", re.M),
        canonical=lambda s: int(s["catalog"]["art_coverage"]["testable_rules"]),
    ),
    # NOTE: STATUS.md displays ART percent as integer ("87%") while README uses
    # "87.4%". The 0.05 float tolerance in check() will not cover that rounding
    # delta, so STATUS percent is intentionally not gated to avoid false
    # positives. The two integer ART counts above (277 / 317) catch any real
    # drift; the percent is derivable from them.

    # ─────────────────────────────────────────────────────────────────────────
    # STATUS.md — counts that were previously ungated (Codex review #3).
    # Canonical sources: catalog.json + dashboard_inventory.json + sentinel_conversion_report.json.
    # ─────────────────────────────────────────────────────────────────────────
    DriftRule(
        label="STATUS: Source Sigma/YAML rules",
        file=STATUS,
        pattern=re.compile(r"^- Source Sigma/YAML rules: (\d+)\s*$", re.M),
        canonical=lambda s: _inv(s, "source_yaml_rules"),
    ),
    DriftRule(
        label="STATUS: Sigma-derived OCI query artifacts",
        file=STATUS,
        pattern=re.compile(r"^- Sigma-derived OCI query artifacts: (\d+)\s*$", re.M),
        canonical=lambda s: _inv(s, "generated_sigma_queries"),
    ),
    DriftRule(
        label="STATUS: Curated analytics total",
        file=STATUS,
        pattern=re.compile(r"^- Curated analytics: (\d+)\s*$", re.M),
        canonical=lambda s: _inv(s, "curated_app_queries") + _inv(s, "generated_hunting_queries"),
        notes="derived: curated_app_queries + generated_hunting_queries",
    ),
    DriftRule(
        label="STATUS: Total query artifacts top-line",
        file=STATUS,
        pattern=re.compile(r"^- Total query artifacts/content items: ([\d,]+)\s*$", re.M),
        canonical=lambda s: _inv(s, "total_query_artifacts"),
    ),
    DriftRule(
        label="STATUS: Dashboards count",
        file=STATUS,
        pattern=re.compile(r"^- Dashboards: (\d+)\s*$", re.M),
        canonical=lambda s: _dash(s, "total_dashboards"),
    ),
    DriftRule(
        label="STATUS: Saved searches (active widgets)",
        file=STATUS,
        pattern=re.compile(r"^- Saved searches: (\d+) active dashboard saved searches;", re.M),
        canonical=lambda s: _dash(s, "total_widgets"),
        notes="dashboard_inventory.summary.total_widgets == saved-search count",
    ),
    DriftRule(
        label="STATUS: Sentinel live validation passed",
        file=STATUS,
        pattern=re.compile(r"Sentinel live validation: (\d+) / \d+ locally clean conversions", re.M),
        canonical=lambda s: _sent(s, "live_validation_passed"),
    ),
    DriftRule(
        label="STATUS: Sentinel locally clean total",
        file=STATUS,
        pattern=re.compile(r"Sentinel live validation: \d+ / (\d+) locally clean conversions", re.M),
        canonical=lambda s: _sent(s, "live_validation_passed") + _sent(s, "live_validation_failed"),
        notes="derived: passed + failed = total submitted to live validator",
    ),
    DriftRule(
        label="STATUS: Sentinel live failures",
        file=STATUS,
        pattern=re.compile(r"(\d+) live failures remain in `queries/sentinel_conversion_report\.json`", re.M),
        canonical=lambda s: _sent(s, "live_validation_failed"),
    ),

    # ── README counts that were also ungated (dashboard + saved-search + widget counts) ──
    DriftRule(
        label="README: Dashboards count",
        file=README,
        pattern=re.compile(r"\*\*Dashboard inventory:\*\* (\d+) dashboards with ", re.M),
        canonical=lambda s: _dash(s, "total_dashboards"),
    ),
    DriftRule(
        label="README: active dashboard saved searches",
        file=README,
        pattern=re.compile(r"\*\*Dashboard inventory:\*\* \d+ dashboards with (\d+) active dashboard saved searches", re.M),
        canonical=lambda s: _dash(s, "total_widgets"),
    ),
    DriftRule(
        label="README: advanced visualization widgets",
        file=README,
        pattern=re.compile(r"and (\d+) advanced visualization widgets", re.M),
        canonical=lambda s: _dash(s, "advanced_visualization_widgets"),
    ),
]


def check(sources: dict) -> list[dict]:
    """Returns list of drift records. Empty list = no drift."""
    drift: list[dict] = []
    for rule in DRIFT_RULES:
        text = rule.file.read_text(encoding="utf-8")
        match = rule.pattern.search(text)
        if not match:
            drift.append({
                "label": rule.label,
                "file": rule.file.name,
                "status": "MISSING",
                "detail": "regex did not match — README/STATUS section may have been renamed",
            })
            continue
        published_raw = match.group(1).replace(",", "")
        canonical_val = rule.canonical(sources)
        # Float-tolerant compare (ART percent uses 1 decimal place in README).
        if isinstance(canonical_val, float):
            published: float | int = float(published_raw)
            mismatch = abs(published - canonical_val) > 0.05
        else:
            published = int(published_raw)
            canonical_val = int(canonical_val)
            mismatch = published != canonical_val
        if mismatch:
            drift.append({
                "label": rule.label,
                "file": rule.file.name,
                "status": "DRIFT",
                "published": published,
                "canonical": canonical_val,
                "delta": round(canonical_val - published, 2),
            })
    return drift


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--report", action="store_true", help="report drift but exit 0")
    parser.add_argument("--json", action="store_true", help="machine-readable JSON output")
    args = parser.parse_args()

    missing = [p for p in (CATALOG, DASHBOARD_INV, SENTINEL_REPORT) if not p.exists()]
    if missing:
        for p in missing:
            print(f"ERROR: {p.relative_to(REPO)} not found. Run the catalog/inventory/sentinel generators first.",
                  file=sys.stderr)
        return 2

    sources = {
        "catalog": json.loads(CATALOG.read_text(encoding="utf-8")),
        "dashboard": json.loads(DASHBOARD_INV.read_text(encoding="utf-8")),
        "sentinel": json.loads(SENTINEL_REPORT.read_text(encoding="utf-8")),
    }
    drift = check(sources)

    if args.json:
        print(json.dumps({"drift_count": len(drift), "items": drift}, indent=2))
    else:
        if not drift:
            print(f"OK — {len(DRIFT_RULES)} inventory counts match queries/catalog.json")
        else:
            print(f"DRIFT DETECTED: {len(drift)} / {len(DRIFT_RULES)} reconciliation rules failed\n")
            for d in drift:
                if d["status"] == "MISSING":
                    print(f"  [MISSING] {d['file']}: '{d['label']}' — {d['detail']}")
                else:
                    sign = "+" if d["delta"] > 0 else ""
                    print(f"  [DRIFT]   {d['file']}: '{d['label']}' "
                          f"published={d['published']} canonical={d['canonical']} ({sign}{d['delta']})")
            print("\nFix: update README.md/STATUS.md to match queries/catalog.json, "
                  "or regenerate catalog via scripts/generate_catalog.py.")

    if drift and not args.report:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
