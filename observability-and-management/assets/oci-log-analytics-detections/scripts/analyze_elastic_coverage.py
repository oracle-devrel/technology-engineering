#!/usr/bin/env python3
"""Coverage gap analyzer: compare MITRE technique coverage against Elastic's detection rules.

Reads Elastic detection-rules TOML files and cross-references against our
canonical catalog (falling back to manifest.json for older checkouts) to
identify MITRE techniques we're missing.

Usage:
  python3 scripts/analyze_elastic_coverage.py --repo /path/to/elastic/detection-rules
  python3 scripts/analyze_elastic_coverage.py --offline   # Use built-in technique catalog
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
CATALOG_PATH = PROJECT_DIR / "queries" / "catalog.json"
MANIFEST_PATH = PROJECT_DIR / "queries" / "manifest.json"

# Built-in catalog of Elastic Windows rule technique coverage (from analysis of 463 rules).
# Used in --offline mode when the Elastic repo is not available locally.
ELASTIC_WINDOWS_TECHNIQUES = {
    "credential_access": {
        "T1003": "OS Credential Dumping", "T1003.001": "LSASS Memory",
        "T1003.002": "Security Account Manager", "T1003.003": "NTDS",
        "T1003.004": "LSA Secrets", "T1003.006": "DCSync",
        "T1110": "Brute Force", "T1110.003": "Password Spraying",
        "T1552": "Unsecured Credentials", "T1552.001": "Credentials In Files",
        "T1555": "Credentials from Password Stores", "T1555.003": "Credentials from Web Browsers",
        "T1556": "Modify Authentication Process", "T1558": "Steal or Forge Kerberos Tickets",
        "T1558.003": "Kerberoasting", "T1558.004": "AS-REP Roasting",
        "T1557": "Adversary-in-the-Middle", "T1539": "Steal Web Session Cookie",
        "T1187": "Forced Authentication", "T1649": "Steal or Forge Authentication Certificates",
    },
    "defense_evasion": {
        "T1027": "Obfuscated Files or Information", "T1027.010": "Command Obfuscation",
        "T1036": "Masquerading", "T1036.003": "Rename System Utilities",
        "T1036.005": "Match Legitimate Name or Location",
        "T1055": "Process Injection", "T1055.001": "DLL Injection",
        "T1055.012": "Process Hollowing", "T1070": "Indicator Removal",
        "T1070.001": "Clear Windows Event Logs", "T1070.004": "File Deletion",
        "T1070.006": "Timestomp", "T1112": "Modify Registry",
        "T1127": "Trusted Developer Utilities Proxy Execution",
        "T1127.001": "MSBuild", "T1140": "Deobfuscate/Decode Files",
        "T1197": "BITS Jobs", "T1202": "Indirect Command Execution",
        "T1218": "System Binary Proxy Execution", "T1218.001": "Compiled HTML File",
        "T1218.003": "CMSTP", "T1218.004": "InstallUtil",
        "T1218.005": "Mshta", "T1218.009": "Regsvcs/Regasm",
        "T1218.010": "Regsvr32", "T1218.011": "Rundll32",
        "T1220": "XSL Script Processing", "T1221": "Template Injection",
        "T1222": "File and Directory Permissions Modification",
        "T1480": "Execution Guardrails", "T1497": "Virtualization/Sandbox Evasion",
        "T1548": "Abuse Elevation Control Mechanism", "T1548.002": "Bypass UAC",
        "T1550": "Use Alternate Authentication Material",
        "T1553": "Subvert Trust Controls", "T1553.004": "Install Root Certificate",
        "T1562": "Impair Defenses", "T1562.001": "Disable or Modify Tools",
        "T1562.002": "Disable Windows Event Logging",
        "T1562.004": "Disable or Modify System Firewall",
        "T1564": "Hide Artifacts", "T1564.001": "Hidden Files and Directories",
        "T1564.003": "Hidden Window", "T1564.004": "NTFS File Attributes",
        "T1574": "Hijack Execution Flow", "T1574.001": "DLL Search Order Hijacking",
        "T1574.002": "DLL Side-Loading", "T1574.011": "Services Registry Permissions Weakness",
        "T1600": "Weaken Encryption", "T1620": "Reflective Code Loading",
    },
    "execution": {
        "T1047": "Windows Management Instrumentation",
        "T1053": "Scheduled Task/Job", "T1053.005": "Scheduled Task",
        "T1059": "Command and Scripting Interpreter",
        "T1059.001": "PowerShell", "T1059.003": "Windows Command Shell",
        "T1059.005": "Visual Basic", "T1059.006": "Python",
        "T1059.007": "JavaScript", "T1106": "Native API",
        "T1129": "Shared Modules", "T1204": "User Execution",
        "T1204.002": "Malicious File", "T1569.002": "Service Execution",
    },
    "persistence": {
        "T1037": "Boot or Logon Initialization Scripts",
        "T1053.005": "Scheduled Task", "T1098": "Account Manipulation",
        "T1136": "Create Account", "T1136.001": "Local Account",
        "T1137": "Office Application Startup", "T1197": "BITS Jobs",
        "T1505.003": "Web Shell", "T1543": "Create or Modify System Process",
        "T1543.003": "Windows Service", "T1546": "Event Triggered Execution",
        "T1546.001": "Change Default File Association",
        "T1546.003": "Windows Management Instrumentation Event Subscription",
        "T1546.011": "Application Shimming", "T1546.015": "COM Hijacking",
        "T1547": "Boot or Logon Autostart Execution",
        "T1547.001": "Registry Run Keys / Startup Folder",
        "T1547.004": "Winlogon Helper DLL", "T1547.009": "Shortcut Modification",
        "T1547.012": "Print Processors", "T1547.014": "Active Setup",
        "T1574.011": "Services Registry Permissions Weakness",
    },
    "privilege_escalation": {
        "T1037": "Boot or Logon Initialization Scripts",
        "T1053.005": "Scheduled Task", "T1068": "Exploitation for Privilege Escalation",
        "T1134": "Access Token Manipulation", "T1134.001": "Token Impersonation/Theft",
        "T1134.002": "Create Process with Token",
        "T1543.003": "Windows Service", "T1546.015": "COM Hijacking",
        "T1547.001": "Registry Run Keys / Startup Folder",
        "T1548.002": "Bypass UAC", "T1574.002": "DLL Side-Loading",
    },
    "lateral_movement": {
        "T1021": "Remote Services", "T1021.001": "Remote Desktop Protocol",
        "T1021.002": "SMB/Windows Admin Shares", "T1021.003": "DCOM",
        "T1021.006": "Windows Remote Management",
        "T1550.002": "Pass the Hash", "T1550.003": "Pass the Ticket",
        "T1570": "Lateral Tool Transfer",
    },
    "discovery": {
        "T1007": "System Service Discovery", "T1012": "Query Registry",
        "T1016": "System Network Configuration Discovery",
        "T1018": "Remote System Discovery", "T1033": "System Owner/User Discovery",
        "T1046": "Network Service Discovery", "T1049": "System Network Connections Discovery",
        "T1057": "Process Discovery", "T1069": "Permission Groups Discovery",
        "T1082": "System Information Discovery", "T1083": "File and Directory Discovery",
        "T1087": "Account Discovery", "T1087.001": "Local Account",
        "T1087.002": "Domain Account", "T1135": "Network Share Discovery",
        "T1201": "Password Policy Discovery", "T1482": "Domain Trust Discovery",
        "T1518": "Software Discovery",
    },
    "impact": {
        "T1485": "Data Destruction", "T1486": "Data Encrypted for Impact",
        "T1489": "Service Stop", "T1490": "Inhibit System Recovery",
        "T1491": "Defacement", "T1496": "Resource Hijacking",
        "T1529": "System Shutdown/Reboot", "T1531": "Account Access Removal",
        "T1561": "Disk Wipe", "T1561.002": "Disk Structure Wipe",
    },
    "collection": {
        "T1005": "Data from Local System", "T1039": "Data from Network Shared Drive",
        "T1056.001": "Keylogging", "T1074.001": "Local Data Staging",
        "T1113": "Screen Capture", "T1114": "Email Collection",
        "T1115": "Clipboard Data", "T1560": "Archive Collected Data",
    },
}


def load_our_techniques():
    """Load MITRE techniques from catalog.json, falling back to manifest.json."""
    if CATALOG_PATH.exists():
        with open(CATALOG_PATH) as f:
            catalog = json.load(f)
        return set(catalog.get("mitre_techniques", []))

    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH) as f:
            manifest = json.load(f)
        return set(manifest.get("mitre_techniques", []))

    print(f"  Warning: neither {CATALOG_PATH} nor {MANIFEST_PATH} exists; running with empty set")
    return set()


def analyze_elastic_repo(repo_path):
    """Scan Elastic detection-rules TOML files for MITRE techniques."""
    elastic_techniques = defaultdict(lambda: defaultdict(str))
    toml_dir = Path(repo_path) / "rules" / "windows"

    if not toml_dir.exists():
        print(f"  Error: {toml_dir} not found")
        return {}

    technique_re = re.compile(r'"(T\d{4}(?:\.\d{3})?)"')
    severity_re = re.compile(r'severity\s*=\s*"(\w+)"')
    tactic_re = re.compile(r'"(TA\d{4})"')

    for toml_path in toml_dir.rglob("*.toml"):
        try:
            content = toml_path.read_text()
            techniques = technique_re.findall(content)
            severity_match = severity_re.search(content)
            severity = severity_match.group(1) if severity_match else "medium"

            for tech in techniques:
                elastic_techniques["windows"][tech] = severity
        except Exception:
            continue

    return dict(elastic_techniques)


def generate_gap_report(our_techniques, elastic_techniques):
    """Generate a gap report showing techniques we're missing."""
    print(f"\n{'=' * 70}")
    print("  MITRE ATT&CK Coverage Gap Report")
    print(f"{'=' * 70}")
    print(f"\n  Our techniques: {len(our_techniques)}")

    total_elastic = set()
    for tactic, techs in elastic_techniques.items():
        total_elastic.update(techs.keys())
    print(f"  Elastic Windows techniques: {len(total_elastic)}")

    gaps = total_elastic - our_techniques
    covered = total_elastic & our_techniques
    print(f"  Covered: {len(covered)}")
    print(f"  Gaps: {len(gaps)}")
    print(f"  Coverage: {len(covered)/len(total_elastic)*100:.1f}%")

    # Group gaps by tactic
    print(f"\n  Gaps by Tactic:")
    print(f"  {'─' * 66}")
    for tactic in sorted(elastic_techniques.keys()):
        techs = elastic_techniques[tactic]
        tactic_gaps = {t: n for t, n in techs.items() if t in gaps}
        if not tactic_gaps:
            continue
        display = tactic.replace("_", " ").title()
        print(f"\n  {display} ({len(tactic_gaps)} gaps):")
        for tech, name in sorted(tactic_gaps.items()):
            print(f"    {tech:12s} {name}")

    return gaps


def main():
    parser = argparse.ArgumentParser(description="Analyze Elastic detection-rules coverage gaps")
    parser.add_argument("--repo", help="Path to elastic/detection-rules repo")
    parser.add_argument("--offline", action="store_true",
                        help="Use built-in technique catalog (no repo needed)")
    args = parser.parse_args()

    our_techniques = load_our_techniques()

    if args.offline or not args.repo:
        print("  Using built-in Elastic Windows technique catalog")
        gaps = generate_gap_report(our_techniques, ELASTIC_WINDOWS_TECHNIQUES)
    else:
        print(f"  Scanning Elastic repo: {args.repo}")
        elastic_techniques = analyze_elastic_repo(args.repo)
        if not elastic_techniques:
            print("  Falling back to built-in catalog")
            elastic_techniques = ELASTIC_WINDOWS_TECHNIQUES
        gaps = generate_gap_report(our_techniques, elastic_techniques)

    print(f"\n  Total gaps to fill: {len(gaps)}")
    print(f"  Use this output to prioritize new rule creation.")


if __name__ == "__main__":
    main()
