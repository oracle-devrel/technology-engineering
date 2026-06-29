#!/usr/bin/env python3
"""Bulk fix rule quality issues: add missing falsepositives and MITRE ATT&CK tags.

Usage:
  python3 scripts/fix_rule_quality.py
  python3 scripts/fix_rule_quality.py --dry-run
"""

import json
import os
import re
import sys
import yaml
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from query_artifacts import is_saved_search_query_file  # noqa: E402

PROJECT_DIR = Path(__file__).parent.parent
RULES_DIR = PROJECT_DIR / "rules"
QUERIES_DIR = PROJECT_DIR / "queries"

# Map rule title patterns to appropriate false positives
FALSEPOSITIVES_MAP = {
    # OCI rules
    r"OCI.*Policy": ["Routine policy changes by authorized administrators", "Automated IaC deployments (Terraform, Pulumi)"],
    r"OCI.*User": ["Routine IAM administration", "Automated provisioning systems"],
    r"OCI.*Group": ["Routine IAM group management", "Automated provisioning systems"],
    r"OCI.*Bucket": ["Routine storage operations by authorized administrators", "Automated backup or archival processes"],
    r"OCI.*Instance": ["Authorized scaling operations", "Automated IaC deployments"],
    r"OCI.*VCN|OCI.*Subnet|OCI.*Security.*List|OCI.*Route": ["Network infrastructure changes during maintenance windows", "Automated IaC deployments"],
    r"OCI.*Internet.*Gateway": ["Planned network architecture changes", "Automated IaC deployments"],
    r"OCI.*Key|OCI.*Vault": ["Scheduled key rotation", "Authorized cryptographic operations"],
    r"OCI.*Login": ["Users with expired passwords or MFA issues", "Scheduled password rotation"],
    r"OCI.*Console": ["Authorized administrator sessions", "Break-glass emergency access"],
    r"OCI.*Audit": ["Compliance-driven audit configuration changes"],
    r"OCI.*Bastion": ["Authorized remote access by operations teams"],
    r"OCI.*Compartment": ["Organizational restructuring", "Automated IaC cleanup"],
    r"OCI.*Database|OCI.*DB": ["Authorized database lifecycle operations", "Test environment cleanup"],
    r"OCI.*Firewall|OCI.*WAF": ["Planned security policy updates", "Automated WAF rule deployments"],
    r"OCI.*Load.*Balancer": ["Infrastructure scaling operations", "Automated IaC deployments"],
    r"OCI.*Log": ["Compliance-driven log management changes"],
    r"OCI.*Notification": ["Authorized monitoring setup"],
    r"OCI.*Object.*Storage": ["Authorized data sharing workflows"],
    r"OCI.*Cross.*Region": ["Planned disaster recovery operations", "Automated backup replication"],
    r"OCI.*MFA": ["Authorized MFA reconfiguration", "Device replacement workflows"],
    r"OCI.*Identity.*Provider|OCI.*Federated": ["Planned identity federation changes"],
    r"OCI.*Function": ["Legitimate serverless operations", "Automated CI/CD pipelines"],
    r"OCI.*Cloud.*Shell": ["Authorized administrator troubleshooting sessions"],
    r"OCI.*Password": ["Scheduled password rotation policies", "New employee onboarding"],
    r"OCI.*Network.*Security": ["Planned security group updates", "Automated IaC deployments"],
    r"OCI.*Customer.*Secret": ["Authorized S3-compatible API access setup"],
    r"OCI.*Auth.*Token": ["Authorized Docker registry or API access setup"],
    r"OCI.*API.*Key": ["Routine API key management for CI/CD systems"],
    r"OCI.*Peering": ["Planned network architecture expansion"],
    r"OCI.*Service.*Gateway": ["Planned private service connectivity setup"],
    r"OCI.*DRG": ["Planned network connectivity expansion"],
    r"OCI.*Metadata": ["Legitimate instance metadata queries by applications"],
    r"OCI.*Replication": ["Planned disaster recovery or compliance-driven replication"],
    # Linux rules
    r"Linux.*SSH": ["Authorized remote administration", "Automated SSH-based deployments"],
    r"Linux.*Sudo": ["Authorized system administration", "Automated maintenance scripts"],
    r"Linux.*Cron": ["Legitimate scheduled maintenance tasks", "Automated system updates"],
    r"Linux.*Container": ["Legitimate container debugging operations"],
    r"Linux.*History": ["Users clearing personal shell history"],
    r"Linux.*Kernel": ["Authorized kernel module management", "System updates"],
    r"Linux.*LD_PRELOAD": ["Legitimate library preloading for testing"],
    r"Linux.*Password|Linux.*Passwd|Linux.*Shadow": ["Authorized password management", "System user provisioning"],
    r"Linux.*Ptrace": ["Legitimate debugging by developers", "Authorized security testing"],
    r"Linux.*Reverse.*Shell": ["Authorized penetration testing"],
    r"Linux.*Authorized.*Key": ["Routine SSH key rotation", "Automated deployment systems"],
    r"Linux.*Suspicious.*Network": ["Legitimate network debugging"],
    r"Linux.*Bind.*Shell": ["Authorized penetration testing"],
    r"Linux.*Crypto": ["Legitimate compute-intensive workloads (ML training, rendering)"],
    r"Linux.*DNS": ["High-volume DNS resolvers", "CDN and caching services"],
    r"Linux.*Download": ["Authorized software installation"],
    r"Linux.*Encrypted.*Channel": ["Legitimate encrypted service communications"],
    r"Linux.*Enumeration": ["Authorized vulnerability assessments"],
    r"Linux.*Exfiltration|Linux.*External": ["Legitimate data transfer operations"],
    r"Linux.*Hidden.*File": ["Build tools and IDEs creating dotfiles"],
    r"Linux.*Hosts.*File": ["Authorized network configuration changes"],
    r"Linux.*Log.*Tamper": ["Log rotation by logrotate"],
    r"Linux.*Network.*Scan": ["Authorized network discovery and monitoring"],
    r"Linux.*Proc.*Mem": ["Legitimate process debugging"],
    r"Linux.*Process.*from.*Dev": ["Legitimate tmpfs usage for build operations"],
    r"Linux.*Proxy|Linux.*Tunnel": ["Authorized VPN or proxy configurations"],
    r"Linux.*Sensitive.*Data": ["Authorized compliance auditing"],
    r"Linux.*Setuid": ["Authorized package installations"],
    r"Linux.*Systemd": ["Authorized service deployment"],
    r"Linux.*Webshell": ["Legitimate web application deployments"],
    r"Linux.*Archive|Linux.*Collected": ["Authorized backup operations"],
    r"Linux.*At.*Job": ["Authorized one-time maintenance tasks"],
    r"Linux.*Bashrc|Linux.*Profile": ["Authorized shell customization by users"],
    r"Linux.*Sudoers": ["Authorized privilege management changes"],
    r"Linux.*Suspicious.*Cron": ["Legitimate cron job updates by administrators"],
    r"Linux.*System.*Owner": ["Authorized system inventory scripts"],
    # Windows rules
    r"Win.*PowerShell|Win.*Powershell": ["Legitimate PowerShell administration scripts", "Automated management tools (SCCM, Intune)"],
    r"Win.*LSASS|Win.*Credential.*Dump|Win.*Mimikatz": ["Authorized penetration testing", "Security tool false positives"],
    r"Win.*UAC": ["Legitimate UAC elevation for software installation"],
    r"Win.*Schtask|Win.*Scheduled": ["Authorized scheduled task creation by administrators"],
    r"Win.*Service": ["Legitimate service installation during software deployment"],
    r"Win.*Registry": ["Authorized registry modifications during software installation"],
    r"Win.*WMI": ["Legitimate WMI usage by management tools"],
    r"Win.*PSExec|Win.*Lateral": ["Authorized remote administration"],
    r"Win.*RDP": ["Authorized remote desktop sessions"],
    r"Win.*Shadow.*Copy": ["Legitimate backup operations"],
    r"Win.*Firewall": ["Authorized firewall rule changes during deployment"],
    r"Win.*Event.*Log": ["Authorized log management operations"],
    r"Win.*LOLBin|Win.*lolbin": ["Legitimate usage of built-in Windows tools by administrators"],
    r"Win.*Kerbero": ["Authorized security assessments"],
    r"Win.*DLL": ["Legitimate DLL loading during software installation"],
    r"Win.*AMSI": ["Security tool testing in lab environments"],
    r"Win.*Encoded": ["Legitimate encoded command usage by management tools"],
    r"Win.*Download": ["Authorized file downloads by administrators"],
    r"Win.*BITS": ["Legitimate BITS transfer for Windows Updates"],
    r"Win.*Net\.exe|Win.*net1": ["Legitimate domain administration"],
    r"Win.*Process.*Hollow|Win.*Process.*Inject": ["Authorized security testing"],
    r"Win.*Access.*Token": ["Legitimate impersonation by service accounts"],
    r"Win.*Screen.*Capture": ["Authorized screen recording tools"],
    r"Win.*Remote.*Access": ["Authorized remote support tools"],
    r"Win.*MSBuild": ["Legitimate build processes in development environments"],
    r"Win.*Certutil": ["Authorized certificate operations"],
    r"Win.*NTDS": ["Authorized domain controller backup operations"],
    r"Win.*Pass.*the.*Hash|Win.*Pass.*the.*Ticket": ["Authorized penetration testing"],
    r"Win.*Wdigest": ["Security testing in lab environments"],
    r"Win.*Spearphishing": ["Legitimate email attachments opening Office applications"],
    r"Win.*Network.*Share": ["Authorized network share enumeration by administrators"],
    r"Win.*Account.*Discovery|Win.*Remote.*System": ["Authorized Active Directory administration"],
    r"Win.*Data.*Stag": ["Legitimate data archival operations"],
    r"Win.*BCDEdit": ["Authorized boot configuration changes"],
    r"Win.*Keylog": ["Authorized input monitoring for compliance"],
    r"Win.*DNS": ["Legitimate DNS traffic", "DNS-based security tools"],
    r"Win.*Beacon|Win.*CobaltStrike|Win.*Cobaltstrike": ["Authorized red team operations"],
    r"Win.*Pipe": ["Legitimate named pipe usage by applications"],
    r"Win.*LDAP": ["Authorized Active Directory queries"],
    r"Win.*SMB": ["Authorized file sharing operations"],
    r"Win.*WinRM": ["Authorized remote management sessions"],
    r"Win.*Outbound": ["Legitimate external service connections"],
    # Suspicious binary rules
    r"Suspicious.*Usage": ["Legitimate usage by system administrators", "Automated system scripts"],
}

# Map rule title patterns to MITRE ATT&CK tags
MITRE_MAP = {
    # OCI audit_events rules
    r"OCI.*AddUserToGroup": ["attack.persistence", "attack.t1098.001"],
    r"OCI.*AttachInternetGateway": ["attack.persistence", "attack.t1583"],
    r"OCI.*CreateBucket": ["attack.collection", "attack.t1530"],
    r"OCI.*CreateGroup": ["attack.persistence", "attack.t1136.003"],
    r"OCI.*CreateInstance": ["attack.resource_development", "attack.t1583.003"],
    r"OCI.*CreateInternetGateway": ["attack.persistence", "attack.t1583"],
    r"OCI.*CreateKey": ["attack.defense_evasion", "attack.t1553"],
    r"OCI.*CreatePolicy": ["attack.privilege_escalation", "attack.t1098"],
    r"OCI.*CreateRouteTable": ["attack.persistence", "attack.t1583"],
    r"OCI.*CreateSecurityList": ["attack.defense_evasion", "attack.t1562.007"],
    r"OCI.*CreateSubnet": ["attack.resource_development", "attack.t1583"],
    r"OCI.*CreateUser": ["attack.persistence", "attack.t1136.003"],
    r"OCI.*CreateVcn": ["attack.resource_development", "attack.t1583"],
    r"OCI.*DeleteBucket": ["attack.impact", "attack.t1485"],
    r"OCI.*DeleteGroup": ["attack.impact", "attack.t1531"],
    r"OCI.*DeleteInternetGateway": ["attack.impact", "attack.t1489"],
    r"OCI.*DeleteKey": ["attack.impact", "attack.t1485"],
    r"OCI.*DeletePolicy": ["attack.impact", "attack.t1531"],
    r"OCI.*DeleteSubnet": ["attack.impact", "attack.t1489"],
    r"OCI.*DeleteUser": ["attack.impact", "attack.t1531"],
    r"OCI.*DeleteVcn": ["attack.impact", "attack.t1489"],
    r"OCI.*DetachInternetGateway": ["attack.impact", "attack.t1489"],
    r"OCI.*RemoveUserFromGroup": ["attack.impact", "attack.t1531"],
    r"OCI.*StartInstance": ["attack.execution", "attack.t1204"],
    r"OCI.*StopInstance": ["attack.impact", "attack.t1489"],
    r"OCI.*TerminateInstance": ["attack.impact", "attack.t1485"],
    r"OCI.*UpdateBucket": ["attack.defense_evasion", "attack.t1562.007"],
    r"OCI.*UpdatePolicy": ["attack.privilege_escalation", "attack.t1098"],
    r"OCI.*UpdateRouteTable": ["attack.defense_evasion", "attack.t1562.007"],
    r"OCI.*UpdateSecurityList": ["attack.defense_evasion", "attack.t1562.007"],
    # OCI detection rules
    r"OCI.*API.*Key": ["attack.persistence", "attack.t1098.001"],
    r"OCI.*Bucket.*Public": ["attack.exfiltration", "attack.t1537"],
    r"OCI.*Compute.*Terminated": ["attack.impact", "attack.t1485"],
    r"OCI.*IAM.*Policy.*Modified|OCI.*Policy.*Change": ["attack.privilege_escalation", "attack.t1098"],
    r"OCI.*Network.*Security.*Group": ["attack.defense_evasion", "attack.t1562.007"],
    r"OCI.*Route.*Table": ["attack.defense_evasion", "attack.t1562.007"],
    r"OCI.*VCN.*Open|OCI.*Security.*List.*Allow": ["attack.defense_evasion", "attack.t1562.007"],
    r"OCI.*WAF": ["attack.defense_evasion", "attack.t1562.007"],
    # Linux rules
    r"Linux.*SSH.*Failed": ["attack.credential_access", "attack.t1110.001"],
    r"Linux.*Sudo": ["attack.privilege_escalation", "attack.t1548.003"],
    # Cloud Guard rules
    r"Cloud Guard.*Audit.*Log.*Retention": ["attack.defense_evasion", "attack.t1562.008"],
    r"Cloud Guard.*Bucket.*Public.*Read": ["attack.exfiltration", "attack.t1537"],
    r"Cloud Guard.*Bucket.*Public.*Write": ["attack.initial_access", "attack.t1190"],
    r"Cloud Guard.*Too.*Many.*Admin": ["attack.privilege_escalation", "attack.t1098"],
    r"Cloud Guard.*API.*Key.*Old": ["attack.credential_access", "attack.t1552.004"],
    r"Cloud Guard.*Console.*Password.*Old": ["attack.credential_access", "attack.t1110"],
    r"Cloud Guard.*Instance.*Principals": ["attack.privilege_escalation", "attack.t1098.001"],
    r"Cloud Guard.*INSTANCE.*PUBLIC.*IP|Cloud Guard.*Instance.*Public": ["attack.initial_access", "attack.t1190"],
    r"Cloud Guard.*Policy.*Too.*Permissive": ["attack.privilege_escalation", "attack.t1098"],
    r"Cloud Guard.*Flow.*Log.*Disabled": ["attack.defense_evasion", "attack.t1562.008"],
    r"Cloud Guard.*Port.*RDP": ["attack.initial_access", "attack.t1133"],
    r"Cloud Guard.*Port.*SSH": ["attack.initial_access", "attack.t1133"],
}


def get_falsepositives(title):
    """Get appropriate false positives for a rule based on its title."""
    for pattern, fps in FALSEPOSITIVES_MAP.items():
        if re.search(pattern, title, re.IGNORECASE):
            return fps
    return ["Authorized administrative operations"]


def get_mitre_tags(title):
    """Get MITRE ATT&CK tags for a rule based on its title."""
    for pattern, tags in MITRE_MAP.items():
        if re.search(pattern, title, re.IGNORECASE):
            return tags
    return None


def fix_yaml_rules(dry_run=False):
    """Fix missing falsepositives and MITRE tags in YAML rules."""
    fixed_fp = 0
    fixed_mitre = 0

    for root, dirs, files in os.walk(RULES_DIR):
        for f in sorted(files):
            if not (f.endswith(".yaml") or f.endswith(".yml")):
                continue
            path = os.path.join(root, f)
            with open(path) as fh:
                content = fh.read()
            rule = yaml.safe_load(content)
            if not rule:
                continue

            title = rule.get("title", "")
            modified = False

            # Fix missing falsepositives
            if not rule.get("falsepositives"):
                fps = get_falsepositives(title)
                rule["falsepositives"] = fps
                modified = True
                fixed_fp += 1

            # Fix missing MITRE tags
            tags = rule.get("tags", [])
            has_mitre = any(t.startswith("attack.t") for t in tags)
            if not has_mitre:
                mitre_tags = get_mitre_tags(title)
                if mitre_tags:
                    existing = set(tags)
                    for t in mitre_tags:
                        if t not in existing:
                            tags.append(t)
                    rule["tags"] = tags
                    modified = True
                    fixed_mitre += 1

            if modified and not dry_run:
                # Remove internal keys before writing
                rule.pop("_path", None)
                with open(path, "w") as fh:
                    yaml.dump(rule, fh, default_flow_style=False,
                              sort_keys=False, allow_unicode=True, width=120)

    return fixed_fp, fixed_mitre


def fix_json_queries(dry_run=False):
    """Fix missing falsepositives in JSON queries."""
    fixed = 0

    for f in sorted(QUERIES_DIR.glob("*.json")):
        if not is_saved_search_query_file(f):
            continue
        with open(f) as fh:
            data = json.load(fh)

        title = data.get("title", "")

        if not data.get("falsepositives"):
            fps = get_falsepositives(title)
            data["falsepositives"] = fps
            fixed += 1

            if not dry_run:
                with open(f, "w") as fh:
                    json.dump(data, fh, indent=2, ensure_ascii=False)

    return fixed


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fix rule quality issues in bulk")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without writing")
    args = parser.parse_args()

    print("=" * 60)
    print("  Rule Quality Fixer")
    print("=" * 60)

    if args.dry_run:
        print("  [DRY RUN MODE]")

    fp_fixed, mitre_fixed = fix_yaml_rules(args.dry_run)
    json_fixed = fix_json_queries(args.dry_run)

    print(f"\n  YAML rules: {fp_fixed} falsepositives added, {mitre_fixed} MITRE tags added")
    print(f"  JSON queries: {json_fixed} falsepositives added")
    print(f"\n  Total fixes: {fp_fixed + mitre_fixed + json_fixed}")


if __name__ == "__main__":
    main()
