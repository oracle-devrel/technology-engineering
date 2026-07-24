#!/usr/bin/env python3
"""Rule quality auditor implementing the Zen of Security Rules principles.

Scans all YAML rules and flags quality issues:
0. Invalid YAML that prevents source rules from loading
1. IOC-only rules (process name match without behavioral context)
2. Missing falsepositives field
3. Missing MITRE tags
4. Duplicate OCL queries
5. Too-broad patterns (single-char wildcards)
6. Silent logsource fallback

Usage:
  python3 scripts/audit_rule_quality.py
  python3 scripts/audit_rule_quality.py --report docs/RULE_QUALITY_REPORT.md
"""

import argparse
import json
import os
import sys
import yaml
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from query_artifacts import is_saved_search_query_file  # noqa: E402

PROJECT_DIR = Path(__file__).parent.parent
RULES_DIR = PROJECT_DIR / "rules"
QUERIES_DIR = PROJECT_DIR / "queries"


def load_all_rules(rules_dir=RULES_DIR):
    """Load all YAML rules with their paths and collect parse failures."""
    rules = []
    errors = []
    for root, dirs, files in os.walk(rules_dir):
        for f in sorted(files):
            if f.endswith(".yaml") or f.endswith(".yml"):
                path = os.path.join(root, f)
                try:
                    with open(path) as fh:
                        rule = yaml.safe_load(fh)
                    if rule:
                        rule["_path"] = path
                        rules.append(rule)
                except Exception as e:
                    print(f"  Error loading {path}: {e}")
                    errors.append({
                        "rule": os.path.relpath(path, rules_dir),
                        "path": path,
                        "issue": f"Invalid YAML: {str(e).splitlines()[0]}",
                        "severity": "critical",
                    })
    return rules, errors


def load_all_queries(queries_dir=QUERIES_DIR):
    """Load all source-derived generated JSON queries."""
    queries = []
    for f in sorted(queries_dir.rglob("*.json")):
        if not is_saved_search_query_file(f):
            continue
        with open(f) as fh:
            data = json.load(fh)
            if not data.get("sigma_id"):
                continue
            data["_file"] = str(f.relative_to(queries_dir))
            queries.append(data)
    return queries


def check_ioc_only(rules):
    """Find rules that match only on process name without behavioral context."""
    issues = []
    for rule in rules:
        detection = rule.get("detection", {})
        condition = detection.get("condition", "")

        # Check if rule only has a simple selection on process_name
        for key, value in detection.items():
            if key == "condition":
                continue
            if isinstance(value, dict):
                keys = list(value.keys())
                if len(keys) == 1 and keys[0] in ("process_name", "Image"):
                    if condition.strip() == key:  # simple "selection" condition
                        issues.append({
                            "rule": rule.get("title", "?"),
                            "path": rule.get("_path", "?"),
                            "issue": f"IOC-only: matches only on {keys[0]}",
                            "severity": "high",
                        })
    return issues


def check_missing_falsepositives(rules):
    """Find rules without a falsepositives field."""
    issues = []
    for rule in rules:
        if not rule.get("falsepositives"):
            issues.append({
                "rule": rule.get("title", "?"),
                "path": rule.get("_path", "?"),
                "issue": "Missing falsepositives field",
                "severity": "medium",
            })
    return issues


def check_missing_mitre_tags(rules):
    """Find rules without MITRE ATT&CK tags."""
    issues = []
    for rule in rules:
        tags = rule.get("tags", [])
        has_mitre = any(t.startswith("attack.t") for t in tags)
        if not has_mitre:
            issues.append({
                "rule": rule.get("title", "?"),
                "path": rule.get("_path", "?"),
                "issue": "No MITRE ATT&CK technique tags",
                "severity": "medium",
            })
    return issues


def check_duplicate_queries(queries):
    """Find queries that produce identical OCL."""
    seen = defaultdict(list)
    for q in queries:
        query = q.get("query", "")
        seen[query].append(q.get("title", "?"))

    issues = []
    for query, titles in seen.items():
        if len(titles) > 1:
            issues.append({
                "rule": ", ".join(titles),
                "path": "",
                "issue": f"Duplicate OCL query ({len(titles)} rules)",
                "severity": "low",
            })
    return issues


def check_broad_patterns(rules):
    """Find rules with overly broad patterns (single-char wildcards)."""
    issues = []
    for rule in rules:
        detection = rule.get("detection", {})
        for key, value in detection.items():
            if key == "condition":
                continue
            if isinstance(value, dict):
                for field, pattern in value.items():
                    if isinstance(pattern, str) and len(pattern) <= 2 and "*" in pattern:
                        issues.append({
                            "rule": rule.get("title", "?"),
                            "path": rule.get("_path", "?"),
                            "issue": f"Too-broad pattern: {field} = '{pattern}'",
                            "severity": "high",
                        })
    return issues


def check_logsource_fallback(queries):
    """Find queries that fell back to default logsource."""
    issues = []
    for q in queries:
        if q.get("logsource_fallback"):
            issues.append({
                "rule": q.get("title", "?"),
                "path": q.get("_file", ""),
                "issue": "Silent logsource fallback to OCI Audit Logs",
                "severity": "medium",
            })
    return issues


def check_missing_stable_id(rules):
    """Find rules without a stable id field."""
    issues = []
    for rule in rules:
        if not rule.get("id"):
            issues.append({
                "rule": rule.get("title", "?"),
                "path": rule.get("_path", "?"),
                "issue": "Missing stable ID field",
                "severity": "low",
            })
    return issues


def check_missing_version(rules):
    """Find rules without a version field."""
    count = sum(1 for r in rules if not r.get("version"))
    if count > 0:
        return [{"rule": f"{count} rules", "path": "", "issue": "Missing version field", "severity": "low"}]
    return []


def generate_report(all_issues, rules, queries, output_path=None):
    """Generate quality report."""
    lines = []
    w = lines.append

    w("# Rule Quality Report")
    w("")
    w(f"> Audited **{len(rules)} rules** and **{len(queries)} queries**")
    w("")

    # Summary by severity
    severity_counts = defaultdict(int)
    for issue in all_issues:
        severity_counts[issue["severity"]] += 1

    w("## Summary")
    w("")
    w(f"| Severity | Count |")
    w("|----------|-------|")
    for sev in ["critical", "high", "medium", "low"]:
        if sev in severity_counts:
            w(f"| {sev.title()} | {severity_counts[sev]} |")
    w(f"| **Total** | **{len(all_issues)}** |")
    w("")

    # Group by check type
    by_issue = defaultdict(list)
    for issue in all_issues:
        category = issue["issue"].split(":")[0] if ":" in issue["issue"] else issue["issue"]
        by_issue[category].append(issue)

    w("## Issues")
    w("")
    for category, issues in sorted(by_issue.items()):
        w(f"### {category} ({len(issues)})")
        w("")
        for issue in issues[:20]:
            w(f"- **{issue['rule']}** — {issue['issue']}")
        if len(issues) > 20:
            w(f"- ... and {len(issues) - 20} more")
        w("")

    report = "\n".join(lines)

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write(report)
        print(f"  Report written to: {output_path}")

    return report


def main():
    parser = argparse.ArgumentParser(description="Audit detection rule quality")
    parser.add_argument("--report", default="docs/RULE_QUALITY_REPORT.md",
                        help="Output report path")
    args = parser.parse_args()

    print("=" * 60)
    print("  Rule Quality Audit")
    print("=" * 60)

    rules, load_errors = load_all_rules()
    queries = load_all_queries()
    print(f"\n  Rules: {len(rules)}")
    print(f"  Queries: {len(queries)}")

    all_issues = list(load_errors)

    print("\n  Running checks:")
    checks = [
        ("IOC-only rules", check_ioc_only, rules),
        ("Missing falsepositives", check_missing_falsepositives, rules),
        ("Missing MITRE tags", check_missing_mitre_tags, rules),
        ("Duplicate queries", check_duplicate_queries, queries),
        ("Broad patterns", check_broad_patterns, rules),
        ("Logsource fallback", check_logsource_fallback, queries),
        ("Missing stable ID", check_missing_stable_id, rules),
        ("Missing version", check_missing_version, rules),
    ]

    for name, check_fn, data in checks:
        issues = check_fn(data)
        all_issues.extend(issues)
        status = f"{len(issues)} issues" if issues else "OK"
        print(f"    {name:30s} {status}")

    if load_errors:
        print(f"    {'Invalid YAML':30s} {len(load_errors)} issues")

    print(f"\n  Total issues: {len(all_issues)}")

    report = generate_report(all_issues, rules, queries, args.report)

    # Print summary
    critical_high = [i for i in all_issues if i["severity"] in ("critical", "high")]
    if critical_high:
        print(f"\n  Critical/High issues: {len(critical_high)}")
        for issue in critical_high[:10]:
            print(f"    - {issue['rule']}: {issue['issue']}")


if __name__ == "__main__":
    main()
