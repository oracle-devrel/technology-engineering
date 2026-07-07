# Threat Hunting Walkthrough

Date: 2026-05-05
Audience: SOC analysts, incident responders, cloud security engineers, demo operators

This guide is the operator walkthrough for the 21-day OCI Log Analytics threat-hunting demo dataset. It shows how to move from alert triage to evidence-backed drilldown across web, endpoint, network, firewall, cloud-control-plane, and application telemetry.

Use the dashboard time range `Last 21 days` for these scenarios. The C2 and web-to-cloud incident widgets are configured with a 21-day saved-search window so the full synthetic campaign remains visible after ingest.

## Data Refresh

Run this flow per OCI profile when preparing a clean demo. Generating per profile keeps synthetic OCI Audit compartment values aligned with the destination tenancy while preserving the same attack story.

```bash
# Generate and ingest into the primary demo profile
env OCI_PROFILE=<OCI_PROFILE_CAP> python3 scripts/setup_log_sources.py
env OCI_PROFILE=<OCI_PROFILE_CAP> python3 scripts/generate_dashboard_data.py --days 21 --geo-interval 15 --validate
env OCI_PROFILE=<OCI_PROFILE_CAP> python3 scripts/ingest_test_data.py --validate
env OCI_PROFILE=<OCI_PROFILE_CAP> python3 scripts/ingest_test_data.py --mode direct
env OCI_PROFILE=<OCI_PROFILE_CAP> python3 scripts/deploy_dashboard.py --cleanup --skip-live-validation --query-lookback 21d --query-timeout 90
env OCI_PROFILE=<OCI_PROFILE_CAP> python3 scripts/verify_deployed_dashboards.py --lookback 21d --query-timeout 90 --max-workers 4 --json docs/health/verify-<profile>-21d-2025-2026.json

# Generate and ingest into DEFAULT
env OCI_PROFILE=DEFAULT python3 scripts/setup_log_sources.py
env OCI_PROFILE=DEFAULT python3 scripts/generate_dashboard_data.py --days 21 --geo-interval 15 --validate
env OCI_PROFILE=DEFAULT python3 scripts/ingest_test_data.py --validate
env OCI_PROFILE=DEFAULT python3 scripts/ingest_test_data.py --mode direct
env OCI_PROFILE=DEFAULT python3 scripts/deploy_dashboard.py --cleanup --skip-live-validation --query-lookback 21d --query-timeout 90
env OCI_PROFILE=DEFAULT python3 scripts/verify_deployed_dashboards.py --lookback 21d --query-timeout 90 --max-workers 4 --json docs/health/verify-default-21d-2025-2026.json
```

If `.env.local` contains profile-specific OCIDs, keep explicit environment overrides in the shell for the target profile. Do not mix one OCI profile with another tenancy or Log Analytics log-group environment variables.

## MELTS Threat-Hunting Method

Use `SOC: 2025-2026 Threat Hunting Dashboard` when you want to run the demo with a MELTS flow: Metrics, Events, Logs, Traces, and Security state. This adapts the common MELT observability model to SOC hunting by adding the security-state layer that answers who is compromised, what data moved, and what containment should happen.

1. **Metrics**: Start with `MELTS: Signal Overview` and `MELTS: Attack Timeline`.
   Use event counts and time buckets to identify the highest-volume stage and the first-seen source.
2. **Events**: Open the attack-specific widgets.
   Review process creations, WAF detections, authentication events, object access, and network sessions.
3. **Logs**: Pivot into the raw log rows behind the widget.
   Confirm the parser fields and the original vendor-shaped record: Windows Security/Sysmon, WAF, Load Balancer, application telemetry, OCI Audit, VCN Flow, and Network Firewall.
4. **Traces**: Use `MELTS: Attack Path Link`.
   Group evidence by deterministic trace IDs: `trace_clickfix_2026_001`, `trace_toolshell_sp_001`, `trace_rmm_2025_001`, `trace_aitm_token_2026_001`, and `trace_w2c_entry_001`.
5. **Security State**: Finish with `Compromised Machines and Data`.
   Record the entry point, compromised host, abused identity, C2 or exfil destination, object names, and containment action.

Research sources used for the 2025-2026 content:

- MELT observability framing: `https://www.splunk.com/en_us/blog/learn/melt-observability.html`
- Microsoft ClickFix analysis: `https://www.microsoft.com/en-us/security/blog/2025/08/21/think-before-you-clickfix-analyzing-the-clickfix-social-engineering-technique/`
- Microsoft CrashFix / Python RAT analysis: `https://www.microsoft.com/en-us/security/blog/2026/02/05/clickfix-variant-crashfix-deploying-python-rat-trojan/`
- Microsoft SharePoint CVE-2025-53770 guidance: `https://www.microsoft.com/en-us/msrc/blog/2025/07/customer-guidance-for-sharepoint-vulnerability-cve-2025-53770`
- Microsoft AiTM token-compromise campaign analysis: `https://www.microsoft.com/en-us/security/blog/2026/05/04/breaking-the-code-multi-stage-code-of-conduct-phishing-campaign-leads-to-aitm-token-compromise/`
- CISA RMM security guidance: `https://www.cisa.gov/resources-tools/resources/remote-monitoring-and-management-rmm-software-security-guidance`

## Scenario 1: Web-to-Cloud Compromise

### Attack Description

An attacker at `203.0.113.50` sends an SSRF payload to the CRM avatar endpoint. The payload reaches the OCI instance metadata service at `169.254.169.254`, the application host `app-prod-02` stages `customer-export-2026-05.csv`, and the compromised service identity `compromised-svc@corp.example.com` reads from Object Storage. Network telemetry then shows egress from `10.0.1.50` to `198.51.100.77`, with Network Firewall evidence for suspicious data exfiltration.

Primary pivots:

| Pivot | Value |
|---|---|
| Trace ID | `trace_w2c_entry_001` |
| Attacker IP | `203.0.113.50` |
| Compromised host | `app-prod-02` |
| Compromised private IP | `10.0.1.50` |
| Windows C2 host | `SRV01.sevenkingdoms.local` |
| Windows C2 private IP | `10.0.1.66` |
| C2 destination | `198.51.100.77` / `updates.cdn-check.example` |
| Abused identity | `compromised-svc@corp.example.com` |
| Bucket and object | `prod-customer-backups/customer-export-2026-05.csv` |

### Walkthrough

1. Open `SOC: Web-to-Cloud Threat Hunting Dashboard`.
2. Set the dashboard to `Last 21 days`.
3. Start with `W2C: Correlated Timeline`.
   Confirm that the same trace or pivot values appear across WAF, load balancer, application, Linux, VCN Flow, Network Firewall, Sysmon, and OCI Audit sources.
4. Open `W2C: Entry Point and SSRF`.
   Look for `Client IP = 203.0.113.50`, a request URL containing `169.254.169.254`, and WAF action `DETECT`.
5. Open `W2C: Compromised Machines`.
   Confirm `app-prod-02`, `10.0.1.50`, and `SRV01.sevenkingdoms.local`.
6. Open `W2C: Compromised Identity`.
   Confirm Object Storage list/read actions from `compromised-svc@corp.example.com`.
7. Open `W2C: VCN Egress` and `W2C: Network Firewall C2`.
   Use `Bytes Sent`, `Destination IP`, `Firewall Rule`, and `Threat Name` to prove the outbound transfer path.
8. Open `W2C: Exfiltrated Data`.
   Tie the data object, principal, destination IP, and trace together.
9. Finish with `W2C: Attack Path Link` and `W2C: MITRE Stage Breakdown`.
   Use the link view for entity-to-entity flow and the sunburst for source/stage coverage.

Expected conclusion:

The entry point was an SSRF request to the CRM app. The compromised machine was `app-prod-02` / `10.0.1.50`. The abused identity was `compromised-svc@corp.example.com`. The exfiltrated object was `customer-export-2026-05.csv`. The outbound destination was `198.51.100.77`.

## Scenario 2: C2 and Beaconing

### Attack Description

Multiple hosts issue suspicious DNS queries and HTTPS callbacks associated with dynamic DNS, high-risk TLDs, and the web-to-cloud exfiltration destination. The campaign includes `evil-c2.duckdns.org`, `beacon.malware.xyz`, `c2.attacker.top`, and `updates.cdn-check.example`, plus VCN Flow and Network Firewall evidence for `198.51.100.77`.

### Walkthrough

1. Open `C2 & Beaconing Detection`.
2. Set time range to `Last 21 days`.
3. Open `Top C2 DNS Domains`.
   Identify suspicious DNS domains and the relative query volume.
4. Open `DNS Beacon Sources`.
   Pivot from domain to source process and host.
5. Open `Beacon Activity Timeline`.
   Find recurring hourly or daily callback windows.
6. Open `C2 Destination IPs`.
   Confirm `198.51.100.77`, destination ports, and source IPs.
7. Open `HTTPS Beaconing (Port 443)`.
   Separate regular HTTPS callbacks from ordinary browser traffic.
8. Open `C2 Communication Topology`.
   Use link analysis to connect source IPs to suspicious destinations.

Expected conclusion:

The strongest C2 path is the repeated source-to-destination flow into `198.51.100.77`, supported by DNS, Sysmon network, VCN Flow, and Network Firewall telemetry. The compromised web-to-cloud host and Windows C2 host both appear in the same campaign window.

## Scenario 3: FreeLabFriday Source-Attributed Hunts

### Attack Description

The FreeLabFriday scenario adds training-derived patterns from Black Hills InfoSec FreeLabFriday Labs. The dashboard covers DNS C2, BITS exfiltration, trusted cloud-service exfiltration, domain-fronted C2, vsagent HTTP beaconing, credential stuffing, rogue user persistence, and port knocking. Each `queries/hunting/flf_*.json` analytic includes a `references` entry pointing to the exact upstream GitHub source path.

### Walkthrough

1. Open `SOC: FreeLabFriday Threat Hunting Dashboard`.
2. Set time range to `Last 21 days`.
3. Start with `FLF: vsagent HTTP Beaconing`.
   Confirm repeated `/beacon` requests with `User Agent = vsagent/1.0`, then pivot to the POST output events.
4. Open `FLF: Port Knocking Sequence`.
   Use link analysis to compare the successful `10.42.0.7 -> 192.0.2.55` sequence against the failed `198.51.100.12` wrong-order sequence.
5. Open `FLF: Domain Fronting CDN C2`.
   Identify non-browser processes reaching CDN/cloud worker endpoints over HTTPS.
6. Open `FLF: Cloud Service Exfiltration` and `FLF: BITS Exfiltration`.
   Compare cloud API traffic and BITS command lines to determine whether the data movement is legitimate sync activity or attacker-controlled transfer.
7. Open `FLF: Credential Stuffing` and `FLF: New User Persistence`.
   Look for automated login attempts across many accounts and any account-creation event that follows suspicious access.

Expected conclusion:

The FreeLabFriday dashboard provides source-attributed, scenario-level pivots. Use it to demonstrate how a training card or packet-capture lab becomes a practical OCI Log Analytics hunt with dashboard prompts, references, and matching synthetic evidence.

## Scenario 4: Active Directory Credential Attack

### Attack Description

The Windows security dataset includes Kerberoasting, Golden Ticket style ticket activity, DCSync replication requests, Pass-the-Ticket/explicit credential use, Credential Manager reads, security group enumeration, and lateral logon sweeps. These attacks model the identity phase after an endpoint foothold.

### Walkthrough

1. Open `SOC: Windows Advanced Threats Dashboard`.
2. Start with Kerberoasting widgets.
   Look for RC4 service ticket requests, SPN sweeps, and a single account requesting many service tickets.
3. Move to Golden Ticket widgets.
   Look for anomalous ticket requests and RC4-encrypted TGT activity.
4. Open DCSync widgets.
   Confirm replication operations from a non-domain-controller account.
5. Open Pass-the-Ticket and explicit credential widgets.
   Look for excessive logon activity and reused credential patterns.
6. Open Credential Manager and group enumeration widgets.
   Use high-frequency credential reads and rapid group membership queries as supporting evidence.
7. Pivot to `SOC: Sysmon Network and Lateral Movement Dashboard`.
   Confirm SMB, WinRM, RDP, LDAP, and Kerberos network evidence.

Expected conclusion:

The campaign shows credential theft and domain escalation behavior rather than isolated failed logons. The strongest hypothesis is a post-compromise identity attack chain: Kerberoasting or credential extraction, privileged ticket use, directory replication, and lateral movement.

## Scenario 5: BLUELIGHT APT37

### Attack Description

The BLUELIGHT scenario models APT37 activity across browser exploitation, suspicious browser child processes, obfuscated command execution, Graph API C2, WMI and registry discovery, screen capture, browser credential access, tool transfer, and OneDrive/Graph exfiltration.

### Walkthrough

1. Open `SOC: APT Detection Dashboard`.
2. Start with `BLUELIGHT: Total Detections`, `BLUELIGHT: Top Affected Hosts`, and `BLUELIGHT: Kill Chain Timeline`.
3. Open `APT37: Drive-by Compromise`.
   Confirm `iexplore.exe` reaching non-Microsoft domains.
4. Open `APT37: Browser Child Process` and `APT37: Obfuscated Commandline`.
   Look for `cmd.exe`, `powershell.exe`, `wscript.exe`, encoded commands, and XOR/Base64 indicators.
5. Open `APT37: Graph API C2` and `YARA: Google App C2`.
   Confirm non-standard processes communicating with cloud APIs.
6. Open discovery and collection widgets.
   Review WMI system enumeration, registry enumeration, file discovery, and screen capture evidence.
7. Open credential and exfiltration widgets.
   Review browser memory access and OneDrive/Graph upload evidence.
8. Finish with `BLUELIGHT: Attack Path`.
   Use link analysis to narrate one affected host from initial browser execution through exfiltration.

Expected conclusion:

The BLUELIGHT dashboard provides a full APT kill-chain view, not a single malware IOC. Treat a host with three or more BLUELIGHT stages as compromised and ready for containment.

## Scenario 6: Linux Persistence and Exfiltration

### Attack Description

Linux telemetry models persistence through cron/systemd/profile changes, privilege escalation through sudo and GTFOBins, local sensitive data collection, archive staging, proxy or tunneling tooling, and exfiltration over alternate protocols.

### Walkthrough

1. Open `SOC: Linux Advanced Threats Dashboard`.
2. Review persistence widgets first.
   Look for cron, shell profile, systemd, and SSH key changes.
3. Review command and privilege widgets.
   Confirm sudo abuse, suspicious command lines, and GTFOBins patterns.
4. Open data collection and archive widgets.
   Look for sensitive path access and archive creation under `/tmp`.
5. Open C2/proxy/tunnel widgets.
   Confirm encrypted C2, DNS tunneling, or proxy tooling.
6. Pivot to `SOC: Threat Hunting Dashboard`.
   Use `Hunt: Linux Persistence Score` and `Hunt: Linux Multi-Stage Attack` to prioritize hosts with multiple Linux indicators.

Expected conclusion:

The Linux path should surface both persistence and data movement. A host that shows persistence plus archive creation plus outbound tunneling is a stronger compromise candidate than a host with a single suspicious command.

## Scenario 7: Browser and Application Attacks

### Attack Description

The browser and application telemetry surface detects client-side and app-layer attacks that WAF alone does not fully explain: XSS, SQL injection, DOM manipulation, session hijacking, suspicious JavaScript, browser fingerprinting, application brute force, slow requests, WAF correlation, and cross-service trace correlation.

### Walkthrough

1. Open `SOC: Browser Attack Detection Dashboard`.
2. Start with the total attack KPI and OWASP breakdown.
3. Open XSS, SQL injection, DOM attack, session hijacking, suspicious JavaScript, and fingerprinting widgets.
4. Pivot to `OCI-DEMO: Application 360 Monitoring Dashboard`.
5. Open `App: WAF Signal Correlation`.
   Confirm the same trace or request path appears in application and WAF telemetry.
6. Open `App: Cross-Service Trace Correlation` and `App: DB Performance Correlation`.
   Determine whether malicious traffic affected application performance.

Expected conclusion:

The app/browser scenario shows how a SOC analyst can move from attack category to impacted service, trace ID, and backend dependency without leaving OCI Log Analytics.

## Scenario 8: 2025-2026 Modern Attack Campaigns

### Attack Descriptions

This dashboard contains five source-attributed modern attack families and one end-to-end data-loss drilldown:

| Attack | Description | Primary Pivots |
|---|---|---|
| ClickFix fake CAPTCHA | Browser social engineering instructs a user to run a clipboard or verification command. The demo emits browser-parented PowerShell plus mshta/rundll32 LOLBin payloads. | `trace_clickfix_2026_001`, `WS02.sevenkingdoms.local`, `10.0.2.71`, `captcha-verify.example` |
| CrashFix Python RAT | ClickFix variant where a browser lure leads to Python RAT execution and callback traffic. | `trace_clickfix_2026_001`, `python.exe`, `crashfix.py`, `crashfix-help.example` |
| SharePoint ToolShell | SharePoint exploitation attempts hit ToolPane and `spinstall0.aspx`, then attempt command execution through the webshell path. | `trace_toolshell_sp_001`, `198.51.100.44`, `sharepoint-prod-01`, `/_layouts/15/spinstall0.aspx` |
| RMM abuse | Post-compromise remote access tooling appears through ScreenConnect, AnyDesk, and Atera process/network telemetry. | `trace_rmm_2025_001`, `relay.screenconnect.example`, `rmm-sync.atera.example` |
| AiTM token replay | A code-of-conduct themed identity compromise reuses a cloud session token to enumerate IAM and access Object Storage. | `trace_aitm_token_2026_001`, `codeofconduct-reader@corp.example.com`, `203.0.113.88` |
| Exfiltration after initial access | Network and cloud audit evidence ties ClickFix and web-to-cloud entry points to large outbound transfers and object reads. | `trace_clickfix_2026_001`, `trace_w2c_entry_001`, `203.0.113.202`, `customer-export-2026-05.csv`, `payroll-may-2026.csv` |

### Walkthrough

1. Open `SOC: 2025-2026 Threat Hunting Dashboard`.
2. Set the dashboard to `Last 21 days`.
3. Start with `MELTS: Signal Overview`.
   Identify which attack stage has the highest event count and which log sources participate.
4. Open `MELTS: Attack Timeline`.
   Find the first-seen event for the campaign and note whether the first source is endpoint, web, application, or cloud control plane.
5. Open `MELTS: Attack Path Link`.
   Select one trace ID and confirm it links more than one source. Use `trace_clickfix_2026_001` for endpoint-to-network-to-exfil and `trace_toolshell_sp_001` for web-to-application exploitation.
6. Open `ClickFix: Clipboard PowerShell`.
   Confirm browser-parented PowerShell with ClickFix/fake CAPTCHA/clipboard indicators on `WS02.sevenkingdoms.local`.
7. Open `ClickFix: LOLBin Payloads`.
   Confirm mshta/rundll32 scriptlet execution and remote payload references.
8. Open `CrashFix: Python RAT`.
   Confirm `python.exe`, `crashfix.py`, and outbound callback traffic to `crashfix-help.example`.
9. Open `SharePoint: ToolShell Attempts`.
   Confirm ToolPane and `spinstall0.aspx` activity from `198.51.100.44`, then check whether WAF only detected it or the backend returned a response.
10. Open `SharePoint: Webshell Post-Exploit`.
    Confirm command-execution attempts against `spinstall0.aspx?cmd=whoami`.
11. Open `RMM: Post-Compromise Activity`.
    Confirm ScreenConnect, AnyDesk, or Atera process launches and associated relay domains.
12. Open `Cloud Identity: AiTM Token Abuse`.
    Confirm one principal moves from login to IAM discovery, Object Storage access, and auth-token creation.
13. Open `Exfil: After Initial Access`.
    Tie large VCN/Network Firewall transfers and Object Storage reads to the entry trace.
14. Finish with `Compromised Machines and Data`.
    Record the compromised hosts, identities, destination IPs, data objects, and containment order.

Expected conclusion:

For the modern campaign, the ClickFix entry point compromises `WS02.sevenkingdoms.local` / `10.0.2.71`, leads to CrashFix Python RAT execution, RMM relay traffic, and a 30 MB exfiltration flow to `203.0.113.202`. The SharePoint path shows a separate ToolShell-style web entry point against `sharepoint-prod-01`. The identity path shows `codeofconduct-reader@corp.example.com` performing token-replay style cloud activity and reading `finance-exports/payroll-may-2026.csv`.

## Analyst Checklist

Use this checklist during the live demo:

- Start with the 21-day time range.
- Anchor on deterministic pivots: trace ID, host, source IP, destination IP, object name, principal.
- Use summary tables to find the strongest entity.
- Use link widgets for path reconstruction.
- Use sunburst widgets for evidence coverage across sources and stages.
- End each scenario with the suspected entry point, compromised machines, abused identity, C2 or exfil destination, and recommended containment action.
