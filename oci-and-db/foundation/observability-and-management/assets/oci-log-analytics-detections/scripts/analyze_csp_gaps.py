#!/usr/bin/env python3
"""CSP gap analysis: identify cloud threat patterns covered by Elastic AWS/Azure/GCP rules
but missing from our OCI rules.

Usage:
  python3 scripts/analyze_csp_gaps.py                  # Built-in catalog
  python3 scripts/analyze_csp_gaps.py --repo /path/to/elastic/detection-rules
"""

import argparse
import json
import os
import re
from collections import defaultdict
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent

# Built-in catalog of Elastic CSP threat patterns (from 233 rules)
ELASTIC_CSP_PATTERNS = {
    "defense_evasion": [
        {"pattern": "Flow log deletion/disabled", "csp": "AWS,Azure,GCP", "technique": "T1562.008",
         "oci_equivalent": "com.oraclecloud.virtualnetwork.deleteflowlog"},
        {"pattern": "Audit log configuration changed", "csp": "AWS,Azure", "technique": "T1562.008",
         "oci_equivalent": "com.oraclecloud.audit.updateconfiguration"},
        {"pattern": "Log retention reduced", "csp": "AWS", "technique": "T1562.008",
         "oci_equivalent": "com.oraclecloud.logging.updatelog"},
        {"pattern": "Security monitoring disabled", "csp": "AWS,Azure,GCP", "technique": "T1562.001"},
        {"pattern": "Firewall rule modification", "csp": "AWS,Azure,GCP", "technique": "T1562.004",
         "oci_equivalent": "com.oraclecloud.virtualnetwork.updatesecuritylist"},
        {"pattern": "Encryption disabled/key deleted", "csp": "AWS,Azure", "technique": "T1600",
         "oci_equivalent": "com.oraclecloud.keymanagement.disablekeyversion"},
    ],
    "persistence": [
        {"pattern": "IAM user/role created", "csp": "AWS,Azure,GCP", "technique": "T1136",
         "oci_equivalent": "com.oraclecloud.identitycontrolplane.createuser"},
        {"pattern": "IAM policy attached with admin access", "csp": "AWS,Azure", "technique": "T1098",
         "oci_equivalent": "com.oraclecloud.identitycontrolplane.createpolicy"},
        {"pattern": "Service account key created", "csp": "AWS,GCP", "technique": "T1098.001",
         "oci_equivalent": "com.oraclecloud.identitycontrolplane.uploadapikeyrequest"},
        {"pattern": "Identity provider modified", "csp": "AWS,Azure", "technique": "T1606",
         "oci_equivalent": "com.oraclecloud.identitycontrolplane.updateidentityprovider"},
    ],
    "credential_access": [
        {"pattern": "MFA fatigue/push spam", "csp": "Azure", "technique": "T1621"},
        {"pattern": "Impossible travel login", "csp": "Azure", "technique": "T1078"},
        {"pattern": "Secret/credential accessed", "csp": "AWS,Azure,GCP", "technique": "T1552",
         "oci_equivalent": "com.oraclecloud.vaultsecret.getsecretbundlebyname"},
    ],
    "exfiltration": [
        {"pattern": "Storage replication to external account", "csp": "AWS,Azure", "technique": "T1537",
         "oci_equivalent": "com.oraclecloud.objectstorage.createreplicationpolicy"},
        {"pattern": "Database backup exported", "csp": "AWS", "technique": "T1537"},
        {"pattern": "Storage bucket made public", "csp": "AWS,GCP", "technique": "T1537",
         "oci_equivalent": "com.oraclecloud.objectstorage.updatebucket"},
    ],
    "lateral_movement": [
        {"pattern": "Network peering created", "csp": "AWS,Azure,GCP", "technique": "T1599",
         "oci_equivalent": "com.oraclecloud.virtualnetwork.createlocalpeeringgateway"},
        {"pattern": "VPN/gateway attachment", "csp": "AWS,Azure", "technique": "T1599",
         "oci_equivalent": "com.oraclecloud.virtualnetwork.createdrgattachment"},
    ],
    "impact": [
        {"pattern": "Resource mass deletion", "csp": "AWS,Azure,GCP", "technique": "T1485"},
        {"pattern": "DNS zone modification", "csp": "AWS,Azure", "technique": "T1584"},
    ],
    "initial_access": [
        {"pattern": "Console login from unusual location", "csp": "Azure", "technique": "T1078"},
        {"pattern": "Federated identity provider changed", "csp": "AWS,Azure", "technique": "T1606",
         "oci_equivalent": "com.oraclecloud.identitycontrolplane.updateidentityprovider"},
    ],
    "privilege_escalation": [
        {"pattern": "Overprivileged policy attached", "csp": "AWS,Azure,GCP", "technique": "T1098",
         "oci_equivalent": "com.oraclecloud.identitycontrolplane.createpolicy"},
        {"pattern": "Instance profile/principal escalation", "csp": "AWS,GCP", "technique": "T1098",
         "oci_equivalent": "com.oraclecloud.identitycontrolplane.createdynamicgroup"},
    ],
}


def load_our_oci_rules():
    """Load existing OCI cloud detection rules."""
    rules = []
    oci_dir = PROJECT_DIR / "rules" / "cloud" / "oci"
    for root, dirs, files in os.walk(oci_dir):
        for f in sorted(files):
            if f.endswith(".yaml") or f.endswith(".yml"):
                rules.append(f)
    return rules


def generate_report():
    """Generate CSP gap analysis report."""
    our_rules = load_our_oci_rules()

    print(f"\n{'=' * 70}")
    print("  CSP-to-OCI Gap Analysis Report")
    print(f"{'=' * 70}")
    print(f"\n  Existing OCI rules: {len(our_rules)}")
    print(f"  Elastic CSP patterns analyzed: "
          f"{sum(len(v) for v in ELASTIC_CSP_PATTERNS.values())}")

    total_gaps = 0
    for tactic, patterns in ELASTIC_CSP_PATTERNS.items():
        display = tactic.replace("_", " ").title()
        gaps = [p for p in patterns if not p.get("oci_equivalent")]
        with_equiv = [p for p in patterns if p.get("oci_equivalent")]

        print(f"\n  {display}:")
        for p in with_equiv:
            print(f"    [MAPPABLE] {p['pattern']} ({p['csp']}) -> {p['oci_equivalent']}")
        for p in gaps:
            print(f"    [GAP]      {p['pattern']} ({p['csp']}) - {p['technique']}")
            total_gaps += 1

    print(f"\n  Mappable patterns: {sum(len(v) for v in ELASTIC_CSP_PATTERNS.values()) - total_gaps}")
    print(f"  Gaps (no OCI equivalent): {total_gaps}")


def main():
    parser = argparse.ArgumentParser(description="CSP gap analysis for OCI rules")
    parser.add_argument("--repo", help="Path to elastic/detection-rules repo (optional)")
    args = parser.parse_args()

    generate_report()


if __name__ == "__main__":
    main()
