#!/usr/bin/env python3
"""
Sync detection rules from the SigmaHQ repository.

Clones/pulls the official SigmaHQ sigma repository and identifies rules
that can be adapted for OCI Log Analytics. Filters by log source
compatibility (Linux, Windows process creation, cloud) and converts
matching rules using the project's Sigma-to-OCL converter.

Usage:
  python3 scripts/sync_sigmahq.py                  # Full sync
  python3 scripts/sync_sigmahq.py --dry-run         # Preview only
  python3 scripts/sync_sigmahq.py --category linux   # Sync specific category
  python3 scripts/sync_sigmahq.py --list-new         # List new rules not yet imported
  python3 scripts/sync_sigmahq.py --since 2026-01-01 # Only rules modified after date
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import yaml
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
RULES_DIR = PROJECT_DIR / "rules"
CONFIG_PATH = PROJECT_DIR / "config" / "sigma_oci_mapping.yaml"
SIGMAHQ_DIR = PROJECT_DIR / ".sigmahq"
SIGMAHQ_REPO = "https://github.com/SigmaHQ/sigma.git"

# SigmaHQ directories that map to our log source categories
SIGMAHQ_RULE_PATHS = {
    "linux": [
        "rules/linux/process_creation",
        "rules/linux/auditd",
        "rules/linux/builtin",
    ],
    "windows": [
        "rules/windows/process_creation",
        "rules/windows/builtin/security",
        "rules/windows/builtin/system",
    ],
    "cloud": [
        "rules-emerging-threats/cloud",
        "rules/cloud",
    ],
}

# Our target directories for each category
TARGET_DIRS = {
    "linux": RULES_DIR / "linux",
    "windows": RULES_DIR / "windows" / "process_creation",
    "cloud": RULES_DIR / "cloud" / "oci",
}

# Logsource filters — only import rules matching these
COMPATIBLE_LOGSOURCES = {
    "linux": {
        "product": ["linux"],
        "category": ["process_creation", "file_event", "network_connection"],
        "service": ["auditd", "syslog", "auth"],
    },
    "windows": {
        "product": ["windows"],
        "category": ["process_creation"],
        "service": ["sysmon", "security", "system"],
    },
    "cloud": {
        "product": ["oci", "gcp", "aws", "azure"],
    },
}


def clone_or_pull_sigmahq():
    """Clone or update the SigmaHQ repository."""
    if SIGMAHQ_DIR.exists():
        print("  Updating SigmaHQ repository...")
        result = subprocess.run(
            ["git", "-C", str(SIGMAHQ_DIR), "pull", "--quiet"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"  Warning: git pull failed: {result.stderr.strip()}")
            return False
        print("  Repository updated.")
    else:
        print(f"  Cloning SigmaHQ repository to {SIGMAHQ_DIR}...")
        result = subprocess.run(
            ["git", "clone", "--depth", "1", SIGMAHQ_REPO, str(SIGMAHQ_DIR)],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"  Error: git clone failed: {result.stderr.strip()}")
            return False
        print("  Repository cloned.")
    return True


def load_existing_sigma_ids():
    """Load sigma IDs of already-imported rules."""
    ids = set()
    for root, dirs, files in os.walk(RULES_DIR):
        for f in files:
            if f.endswith(".yaml") or f.endswith(".yml"):
                path = os.path.join(root, f)
                try:
                    with open(path) as fh:
                        rule = yaml.safe_load(fh)
                    if rule and rule.get("id"):
                        ids.add(rule["id"])
                except Exception:
                    pass
    return ids


def is_compatible(rule, category):
    """Check if a SigmaHQ rule is compatible with our log sources."""
    logsource = rule.get("logsource", {})
    filters = COMPATIBLE_LOGSOURCES.get(category, {})

    product = logsource.get("product", "")
    cat = logsource.get("category", "")
    service = logsource.get("service", "")

    if "product" in filters:
        if product not in filters["product"]:
            return False

    if "category" in filters and cat:
        if cat not in filters["category"]:
            return False

    if "service" in filters and service:
        if service not in filters["service"]:
            return False

    return True


def adapt_rule_for_oci(rule, category):
    """Adapt a SigmaHQ rule for OCI Log Analytics compatibility.

    Adjusts the logsource mapping to match our project's conventions.
    Preserves original service for Windows Security/System event rules.
    """
    logsource = rule.get("logsource", {})

    if category == "linux":
        logsource["product"] = "linux"
        if not logsource.get("service"):
            logsource["service"] = "syslog"
    elif category == "windows":
        logsource["product"] = "windows"
        # Preserve original service if it's security or system (not sysmon)
        original_service = logsource.get("service", "")
        if original_service in ("security", "system"):
            pass  # keep original service
        elif not original_service:
            logsource["service"] = "sysmon"
        if not logsource.get("category"):
            logsource["category"] = "process_creation"
    elif category == "cloud":
        # Only import OCI-native cloud rules; skip AWS/Azure/GCP
        # (Phase 4 handles CSP mapping with proper OCI equivalents)
        if logsource.get("product") not in ("oci",):
            return None  # signal to skip this rule
        logsource["service"] = "audit"

    rule["logsource"] = logsource
    return rule


def scan_sigmahq_rules(category, since_date=None):
    """Scan SigmaHQ for rules in a given category."""
    rules = []
    paths = SIGMAHQ_RULE_PATHS.get(category, [])

    for rule_path in paths:
        full_path = SIGMAHQ_DIR / rule_path
        if not full_path.exists():
            continue

        for root, dirs, files in os.walk(full_path):
            for f in sorted(files):
                if not (f.endswith(".yaml") or f.endswith(".yml")):
                    continue

                filepath = os.path.join(root, f)

                # Check modification date if filter specified
                if since_date:
                    mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if mtime < since_date:
                        continue

                try:
                    with open(filepath) as fh:
                        rule = yaml.safe_load(fh)
                    if not rule or "detection" not in rule:
                        continue

                    # Check logsource compatibility
                    if not is_compatible(rule, category):
                        continue

                    rule["_source_path"] = filepath
                    rule["_category"] = category
                    rules.append(rule)
                except Exception as e:
                    print(f"  Warning: Could not parse {filepath}: {e}")

    return rules


def import_rule(rule, category, dry_run=False):
    """Import a SigmaHQ rule into our project."""
    target_dir = TARGET_DIRS.get(category, RULES_DIR)

    # Create safe filename
    title = rule.get("title", "untitled")
    safe_name = title.lower().replace(" ", "_").replace(":", "")
    safe_name = "".join(c for c in safe_name if c.isalnum() or c in "_-")
    filename = f"{safe_name}.yaml"
    target_path = target_dir / filename

    if target_path.exists():
        return None  # Skip existing

    # Adapt for OCI LA
    adapted = adapt_rule_for_oci(rule.copy(), category)
    if adapted is None:
        return None  # non-OCI cloud rule, skip

    # Remove internal keys
    adapted.pop("_source_path", None)
    adapted.pop("_category", None)

    if dry_run:
        return str(target_path)

    with open(target_path, "w") as f:
        yaml.dump(adapted, f, default_flow_style=False, sort_keys=False)

    return str(target_path)


def main():
    parser = argparse.ArgumentParser(description="Sync rules from SigmaHQ")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without importing")
    parser.add_argument("--category", choices=["linux", "windows", "cloud"],
                        help="Sync specific category only")
    parser.add_argument("--list-new", action="store_true",
                        help="List new rules not yet imported")
    parser.add_argument("--since", type=str,
                        help="Only rules modified after date (YYYY-MM-DD)")
    parser.add_argument("--limit", type=int, default=0,
                        help="Max rules to import per category (0=unlimited)")
    args = parser.parse_args()

    print("=" * 60)
    print("SigmaHQ Detection Rules Sync")
    print("=" * 60)

    # Parse since date
    since_date = None
    if args.since:
        since_date = datetime.strptime(args.since, "%Y-%m-%d")

    # Clone or update repo
    if not clone_or_pull_sigmahq():
        sys.exit(1)

    # Load existing rule IDs
    existing_ids = load_existing_sigma_ids()
    print(f"\n  Existing rules: {len(existing_ids)}")

    # Determine categories to scan
    categories = [args.category] if args.category else ["linux", "windows", "cloud"]

    total_new = 0
    total_imported = 0

    for category in categories:
        print(f"\n--- {category.upper()} ---")
        rules = scan_sigmahq_rules(category, since_date)
        print(f"  Compatible rules in SigmaHQ: {len(rules)}")

        # Filter out already-imported
        new_rules = [r for r in rules if r.get("id") not in existing_ids]
        print(f"  New (not yet imported): {len(new_rules)}")
        total_new += len(new_rules)

        if args.list_new:
            for r in new_rules[:20]:
                level = r.get("level", "?")
                print(f"    [{level:8s}] {r.get('title', 'untitled')}")
            if len(new_rules) > 20:
                print(f"    ... and {len(new_rules) - 20} more")
            continue

        # Import new rules
        limit = args.limit if args.limit > 0 else len(new_rules)
        imported = 0
        for rule in new_rules[:limit]:
            result = import_rule(rule, category, dry_run=args.dry_run)
            if result:
                prefix = "[DRY RUN] " if args.dry_run else ""
                print(f"  {prefix}Imported: {os.path.basename(result)}")
                imported += 1
                total_imported += 1

        print(f"  Imported: {imported}")

    print(f"\n{'=' * 60}")
    print(f"  New rules available: {total_new}")
    if not args.list_new:
        print(f"  Rules imported: {total_imported}")
        if total_imported > 0 and not args.dry_run:
            print(f"\n  Next steps:")
            print(f"    python3 scripts/convert_sigma.py --validate --stats")
            print(f"    python3 scripts/generate_catalog.py")


if __name__ == "__main__":
    main()
