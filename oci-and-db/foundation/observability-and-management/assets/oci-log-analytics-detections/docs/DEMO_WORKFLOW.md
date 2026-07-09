# OCI Log Analytics Advanced Detection — Demo Workflow

Date: 2026-05-12
Audience: Demo operators, SOC analysts, security architects, platform engineers

## Overview

This document provides a step-by-step demo workflow showcasing OCI Log Analytics advanced detection capabilities deployed as part of the OCI-DEMO platform. The demo covers seven scenarios across 55-65 minutes, progressing from foundational SOC operations to advanced APT threat hunting, browser/application telemetry detection, an end-to-end web-to-cloud incident drilldown, and 2025-2026 MELTS-based attack hunting.

## Current Operator Shortcut

Before the demo, refresh the tenancy with the current dashboard-first path:

```bash
python3 scripts/setup_log_sources.py
python3 scripts/generate_dashboard_data.py --days 21 --geo-interval 15 --validate
python3 scripts/ingest_test_data.py --validate
python3 scripts/ingest_test_data.py --mode direct
python3 scripts/deploy_dashboard.py --cleanup --query-lookback 21d --query-timeout 90
python3 scripts/verify_deployed_dashboards.py --lookback 21d --query-timeout 90 --json docs/health/verify-default-21d-final.json
```

Validated on `2026-05-12` for local generation and live dashboard deployment:

- `221,078` synthetic events generated across `17` files in the latest local 21-day dataset
- `16/16` standard files pass ingest pre-flight validation and direct upload; the scoped Octo APM workshop JSONL is uploaded by the workshop wrapper
- `29` dashboards and `441` active saved searches resolve from generated inventory after the C2, FreeLabFriday, web-to-cloud, browser, APT, application telemetry, 2025-2026 MELTS, Sentinel, and Octo APM updates
- `<OCI_PROFILE_CAP>` has parser/source setup complete, the updated Octo application/APM dataset uploaded, and the current `441` dashboard-widget baseline deployed and live-validated (parse 681/681 PASS)
- Live health is validated with a 21-day lookback after full cleanup redeploys. Regenerate `docs/health/verify-<profile>-21d-final.json` and `docs/health/verify-default-21d-final.json` after deploying the current `22`-dashboard inventory.

The current repository configuration resolves to `29` dashboards and `441` active saved searches. The Octo APM workshop, C2, FreeLabFriday, web-to-cloud, and 2025-2026 drilldown widgets request `l21d` so the full three-week incident remains visible after ingest.

Use this path before recreating dashboards. `deploy_dashboard.py` validates the generated inventory and every unique dashboard query in OCI Log Analytics before importing dashboards or embedded saved searches.

## Prerequisites

| Requirement | Current State |
|-------------|---------------|
| OCI Console access | `https://console.<OCI_REGION>.oraclecloud.com` |
| Demo Controls | `https://<DEMO_CONTROL_PLANE_HOST>` |
| Control Plane | `https://<DEMO_CONTROL_PLANE_HOST>` |
| Log Analytics | <OBSERVABILITY_COMPARTMENT> compartment → Dashboards |
| Test data generated | 221,078 local events across 17 NDJSON datasets |
| Dashboards configured | 29 SOC/demo dashboards + 441 active saved searches |

---

## Demo Scenario 1: SOC Security Overview (5 min)

**Objective:** Show executive-level cross-domain security posture in one view.

### Steps

1. **Open OCI Console** → Observability & Management → Log Analytics → Dashboards
2. **Select compartment:** `<OBSERVABILITY_COMPARTMENT>`
3. **Open:** `SOC Overview Dashboard`

**Talking Points:**
- "This is a unified SOC overview pulling security events from OCI Audit, Windows Sysmon, Linux, Cloud Guard, and WAF — all in one dashboard."
- "Each widget represents a detection rule converted from industry-standard Sigma format into OCI Log Analytics Query Language."
- "The repo currently ships 454 source rules, 476 Sigma-derived OCI query artifacts, 47 curated app/APM analytics, 98 hunting analytics, and 231 MITRE ATT&CK techniques across 14 tactics."

4. **Click into** `SOC: Console Login Failures` — show the OCL query behind it
5. **Show** the hunting widget: `Hunt: SSH Brute Force` — highlight the frequency analysis pattern:
   ```
   | stats count as failed_attempts by 'Client Host'
   | where failed_attempts > 5
   | sort -failed_attempts
   ```

**Key Message:** "Every detection rule has full MITRE ATT&CK mapping, STIG compliance tagging, and validated OCL, and the generated catalog keeps the published inventory in sync with the code."

---

## Demo Scenario 2: Windows Endpoint Threat Detection (10 min)

**Objective:** Demonstrate real-time Windows Sysmon detection with MITRE ATT&CK correlation.

### Steps

1. **Open:** `SOC: Windows Security Dashboard`
   - Set time range to **Last 21 days** (the dashboards default to `l21d`)
   - Point out the widgets are now populated with detection data

2. **Walk through detections:**

   | Widget | What it detects | MITRE |
   |--------|----------------|-------|
   | Win: Encoded PowerShell | Base64-encoded commands hiding malicious payloads | T1059.001 |
   | Win: Credential Dump (LSASS) | procdump/comsvcs targeting LSASS memory | T1003.001 |
   | Win: Certutil Download | LOLBin abuse for payload download/decode | T1105 |
   | Win: Shadow Copy Deletion | Ransomware pre-encryption behavior | T1490 |

3. **Click into** `Win: Encoded PowerShell` → Show the matched events:
   ```
   Process Name: powershell.exe
   Command Line: powershell.exe -NoProfile -NonInteractive -EncodedCommand SQBFAFgA...
   Parent Process Name: cmd.exe
   ```

4. **Navigate to** `SOC: Windows Advanced Threats Dashboard`
   - Show Kerberoasting, Pass-the-Hash, Process Hollowing detections
   - "These cover advanced adversary techniques used in real breaches."

5. **Show** `SOC: Sysmon Network and Lateral Movement Dashboard`
   - C2 beacon detection (periodic outbound HTTPS)
   - SMB/WinRM lateral movement
   - DNS tunneling indicators
   - Named pipe activity (CobaltStrike, PsExec, Mimikatz)

**Key Message:** "Full MITRE ATT&CK coverage from initial access through lateral movement and exfiltration — 249 Windows source rules covering LOLBins, credential theft, persistence, defense evasion, and more."

---

## Demo Scenario 3: APT Threat Hunting — BLUELIGHT RAT (15 min)

**Objective:** Demonstrate APT-specific detection with kill chain correlation and cross-reference to Splunk/KQL queries.

### Background (30 seconds)

> "BLUELIGHT is a Remote Access Trojan attributed to APT37 (InkySquid), a North Korean threat actor. It exploits browser vulnerabilities (CVE-2020-1380, CVE-2021-26411) for initial access and uses Microsoft Graph API and OneDrive for command-and-control and data exfiltration. We've replicated the threat hunting report from markBH1510's research and converted every Splunk detection query into OCI Log Analytics."

### Steps

1. **Open:** `SOC: APT Detection Dashboard`
   - This is a dedicated BLUELIGHT kill chain dashboard with 22 widgets: 5 showcase/correlation widgets plus 17 per-stage detections

2. **Walk the kill chain** (top to bottom):

   | Stage | Dashboard Widget | What to Show |
   |-------|-----------------|--------------|
   | **Initial Access** | APT37: Drive-by Compromise | IE connecting to non-Microsoft domains |
   | **Execution** | APT37: Browser Child Process | iexplore.exe spawning cmd.exe/powershell.exe |
   | **Defense Evasion** | APT37: Obfuscated Commandline | XOR key 0xCF, Base64, encoded commands |
   | **C2** | APT37: Graph API C2 | Non-standard processes connecting to graph.microsoft.com |
   | **Discovery** | APT37: WMI System Discovery | Win32_ComputerSystem enumeration from browser |
   | **Discovery** | APT37: Registry Enumeration | SecurityCenter2, AV product key queries |
   | **Collection** | APT37: Screen Capture | Rapid .jpg creation (>3/minute) |
   | **Credential Access** | APT37: Browser Credential Theft | PROCESS_ALL_ACCESS to browser memory |
   | **C2** | APT37: Ingress Tool Transfer | Executables dropped in Temp/AppData |
   | **Exfiltration** | APT37: OneDrive Exfiltration | Large uploads to graph.microsoft.com |

3. **Show the hunting correlation** — `Hunt: BLUELIGHT Kill Chain`:
   ```
   | stats count as TotalEvents, distinctcount('Event ID') as StageCount
     by 'Host Name (Server)'
   | where StageCount >= 3
   | sort -TotalEvents
   ```
   - "This query correlates multiple kill chain stages on the same host. If a host shows 3 or more BLUELIGHT stages within the time window, it's flagged as a potential compromise."

4. **Click into any rule** → Show the JSON query file:
   - `splunk_original` — the original Splunk SPL query
   - `query` — the converted and validated OCL query
   - `threat_intel` — malware family, MITRE software ID, threat actor, CVEs
   - `mitre_attack` — tactic and technique mapping

5. **Show the Sigma YAML** source rule (optional):
   - Navigate to `rules/windows/apt/bluelight_graph_api_c2.yaml`
   - "Every detection starts as a portable Sigma rule. Our converter handles field mapping, log source resolution, and OCL syntax generation automatically."

**Key Message:** "We took a real APT threat hunting report, converted the BLUELIGHT detection set into OCI Log Analytics, added YARA-backed confirmation logic and kill chain correlation, and deployed it as a production-ready dashboard — complete with Sigma YAML, SPL cross-reference, and threat intelligence metadata."

---

## Demo Scenario 4: Browser Attack Detection via `SOC Application Logs` (10 min)

**Objective:** Show client-side attack detection using the `SOC Application Logs` telemetry surface — a capability that WAF alone cannot provide.

### Steps

1. **Open:** `SOC: Browser Attack Detection Dashboard`

2. **Explain the architecture:**
   > "Traditional SIEMs only see server-side logs. In this demo, browser and application telemetry is normalized into `SOC Application Logs`, a custom OCI Log Analytics source with OpenTelemetry-shaped fields. That lets us detect client-side attacks that WAF can't see — DOM-based XSS, session hijacking, crypto mining scripts, and browser fingerprinting."

3. **Walk through detections:**

   | Widget | Attack Type | What it Detects |
   |--------|-------------|-----------------|
   | Browser: XSS Attack | Cross-Site Scripting | `<script>`, `javascript:`, event handlers in URLs |
   | Browser: SQL Injection | SQL Injection | UNION SELECT, OR 1=1, SLEEP(), INFORMATION_SCHEMA |
   | Browser: Session Hijacking | Session Hijacking | >5 distinct session IDs per source IP in 5 min |
   | Browser: DOM-Based Attacks | DOM XSS | document.cookie, eval(), innerHTML manipulation |
   | Browser: Suspicious JS | Cryptomining/Keylogger | coinhive, cryptonight, keydown event listeners |
   | Browser: Fingerprinting | Reconnaissance | Canvas, WebGL, AudioContext API abuse |

4. **Show the hunting query** — `Hunt: Browser Attack Frequency`:
   - Multi-vector attacker identification
   - "This finds source IPs that are attempting multiple attack types — XSS AND SQLi from the same IP indicates a coordinated attack, not a scanner."

5. **Connect to App 360** — Open `OCI-DEMO: Application 360 Monitoring Dashboard`:
   - Show how application trace telemetry correlates with security events
   - "The same trace ID that shows a slow request in the app telemetry view also shows a WAF block in the security dashboard."

6. **Open the dedicated APM view** — `OCI-DEMO: Octo APM Demo Dashboard`:
   - Show `octo-apm-demo` RED metrics, request/error timeline, span hotspots, trace-to-log correlation, Java/payment/API Gateway errors, OSQuery host evidence, and compromised VM pivots
   - "This view uses the same `Trace ID`, `Span ID`, and metric fields to correlate application logs, APM-shaped spans, and metric samples."

**Key Message:** "Browser-side detection is a significant blind spot for most organizations. By normalizing browser and application telemetry into `SOC Application Logs`, we extend detection from the server all the way to the browser — covering OWASP Top 10 attack patterns that WAF alone cannot see."

---

## Demo Scenario 5: Web-to-Cloud Threat Hunting Drilldown (12 min)

**Objective:** Show a complete threat-hunting investigation from the web entry point through compromised machines, cloud identity abuse, C2, and exfiltrated data.

### Attack Description

| Stage | What Happens | Primary Evidence |
|-------|--------------|------------------|
| **Recon / Entry** | Attacker `<ATTACK_SOURCE_IP>` probes the CRM endpoint and sends an SSRF payload to the instance metadata endpoint. | WAF, Load Balancer, Web Application, Application logs |
| **Host Compromise** | The app host `<APP_HOST>` accesses `<OCI_METADATA_ENDPOINT>`, stages `<OBJECT_EXPORT_NAME>`, and begins outbound transfer. | Linux Secure, Application logs |
| **C2 / Egress** | Private IP `<COMPROMISED_PRIVATE_IP>` communicates with C2 destination `<C2_DESTINATION_IP>`; Windows host `<WINDOWS_HOST>` shows matching outbound C2. | VCN Flow, Network Firewall, Sysmon Network |
| **Cloud Abuse** | Service identity `<COMPROMISED_PRINCIPAL>` lists and reads objects from bucket `<OBJECT_STORAGE_BUCKET>`. | OCI Audit |
| **Exfiltration** | Large outbound byte counts and firewall threat alert identify the exfil destination and object name. | VCN Flow, Network Firewall, OCI Audit, Application logs |

### Steps

1. **Open:** `SOC: Web-to-Cloud Threat Hunting Dashboard`
   - Set time range to **Last 21 days**
   - Start with `W2C: Correlated Timeline`
   - Point out the shared Trace ID: `<TRACE_ID>`

2. **Find the entry point**
   - Open `W2C: Entry Point and SSRF`
   - Show:
     - `Client IP`: `<ATTACK_SOURCE_IP>`
     - `Request URL`: contains `<OCI_METADATA_ENDPOINT>`
     - WAF action `DETECT`, not `BLOCK`
     - Backend/app host context tied to `<APP_HOST>`

3. **Identify compromised machines**
   - Open `W2C: Compromised Machines`
   - Confirm:
     - Linux app host: `<APP_HOST>`
     - Compromised private IP: `<COMPROMISED_PRIVATE_IP>`
     - Windows C2 indicator host: `<WINDOWS_HOST>`
   - Pivot to Linux command lines showing metadata access and export staging.

4. **Confirm cloud identity abuse**
   - Open `W2C: Compromised Identity`
   - Show the abused OCI principal:
     - `<COMPROMISED_PRINCIPAL>`
     - Object Storage actions: list buckets, list objects, get object, create pre-authenticated request
     - Resource: `<OBJECT_STORAGE_EXPORT_PATH>`

5. **Prove C2 and exfiltration**
   - Open `W2C: VCN Egress`
   - Show the large `Bytes Sent` values from `<COMPROMISED_PRIVATE_IP>` to `<C2_DESTINATION_IP>`
   - Open `W2C: Network Firewall C2`
   - Show `Threat Name = Suspicious Data Exfiltration`
   - Open `W2C: Exfiltrated Data`
   - Tie together the object name, service identity, C2 IP, and network byte counts.

6. **Use advanced drilldowns**
   - Open `W2C: Attack Path Link`
   - Show the full path grouped by `Trace ID`, `Log Source`, and `Attack Stage`
   - Open `W2C: MITRE Stage Breakdown`
   - Summarize evidence coverage by attack stage.

**Key Message:** "The demo is not just a set of detections. It is an investigation path: web request, compromised host, abused cloud identity, network egress, firewall alert, and exfiltrated object, all connected by deterministic synthetic telemetry across the last 21 days."

---

## Demo Scenario 6: 2025-2026 MELTS Threat Hunting (10 min)

**Objective:** Show modern 2025-2026 attack detection with MELTS-driven pivots across metrics, events, logs, traces, and security state.

### Attack Description

| Attack | What Happens | Primary Evidence |
|--------|--------------|------------------|
| ClickFix | Fake CAPTCHA lure causes browser-parented PowerShell and LOLBin execution. | Windows Sysmon, Windows Security |
| CrashFix | ClickFix variant launches a Python RAT and HTTPS callback traffic. | Windows Sysmon, Sysmon Network |
| SharePoint ToolShell | ToolPane / `spinstall0.aspx` exploitation and webshell command attempts. | WAF, Load Balancer, Web Application, Application logs |
| RMM Abuse | ScreenConnect, AnyDesk, and Atera appear after compromise. | Windows Sysmon, Sysmon Network |
| AiTM Token Replay | One cloud principal performs login, discovery, Object Storage access, and auth-token creation. | OCI Audit |
| Exfiltration | Large network transfers and Object Storage reads tie the attack to data loss. | VCN Flow, Network Firewall, OCI Audit |

### Steps

1. **Open:** `SOC: 2025-2026 Threat Hunting Dashboard`
   - Set time range to **Last 21 days**
   - Start with `MELTS: Signal Overview`
   - Explain the method: Metrics, Events, Logs, Traces, and Security state

2. **Build the timeline**
   - Open `MELTS: Attack Timeline`
   - Identify the earliest source and the highest-volume stage
   - Pivot into `MELTS: Attack Path Link` and select `trace_clickfix_2026_001`

3. **Investigate ClickFix and CrashFix**
   - Open `ClickFix: Clipboard PowerShell`
   - Confirm browser parent, hidden PowerShell, fake CAPTCHA/clipboard indicators
   - Open `ClickFix: LOLBin Payloads`
   - Confirm mshta/rundll32 execution
   - Open `CrashFix: Python RAT`
   - Confirm `python.exe`, `crashfix.py`, and callback traffic

4. **Investigate SharePoint ToolShell**
   - Open `SharePoint: ToolShell Attempts`
   - Confirm ToolPane and `spinstall0.aspx` requests from `<UNTRUSTED_REDIRECT_IP>`
   - Open `SharePoint: Webshell Post-Exploit`
   - Confirm `spinstall0.aspx?cmd=whoami`

5. **Investigate RMM and identity compromise**
   - Open `RMM: Post-Compromise Activity`
   - Confirm ScreenConnect, AnyDesk, Atera, and relay domains
   - Open `Cloud Identity: AiTM Token Abuse`
   - Confirm `codeofconduct-reader@corp.example.com` and the cloud API sequence

6. **Close with data impact**
   - Open `Exfil: After Initial Access`
   - Identify destination `<EXFIL_DESTINATION_IP>` and large outbound bytes
   - Open `Compromised Machines and Data`
   - State the compromised machines, abused identity, and data objects

**Key Message:** "The dashboard is built for threat hunting, not one-off alerting: it starts from MELTS correlation, then drills into each attack family and ends with compromised machines and exfiltrated data."

---

## Demo Scenario 7: STIG Compliance & Hunting (5 min)

**Objective:** Show compliance monitoring and advanced threat hunting analytics.

### Steps

1. **Open:** `SOC: OCI STIG Compliance Dashboard`
   - "24 detection rules mapped to DoD STIG controls: IA-2 (MFA), SC-7 (network security), AU-11 (audit retention), AC-17 (remote access)."
   - Show `STIG: MFA Disabled`, `STIG: Vault Secret Deleted`, `STIG: Security List All Protocols`

2. **Open:** `SOC: Threat Hunting Dashboard`
   - Walk through hunting methodologies:

   | Method | Query | What It Finds |
   |--------|-------|---------------|
   | Frequency Analysis | SSH Brute Force | IPs with >5 failed SSH logins |
   | Rare Value Stacking | Windows Rare Process | Processes seen <3 times (anomalies) |
   | Anomaly Scoring | Defense Evasion Score | Hosts with multiple evasion techniques |
   | Time-Based | After-Hours IAM Activity | IAM changes outside business hours |
   | Multi-Stage Correlation | Linux Multi-Stage Attack | Hosts with 3+ attack indicators |

**Key Message:** "Compliance isn't just a checkbox — these rules run continuously against live telemetry. And the hunting dashboard uses analytics-driven queries inspired by the Threat Hunter's Cookbook to surface threats that signature-based detection misses."

---

## Quick Reference: Demo Commands

### Trigger Attack Simulation (via Control Plane API)
```bash
# Canonical 21-day dashboard refresh flow for the full web-to-cloud showcase
python3 scripts/setup_log_sources.py
python3 scripts/generate_dashboard_data.py --days 21 --geo-interval 15 --validate
python3 scripts/ingest_test_data.py --validate
python3 scripts/ingest_test_data.py --mode direct
python3 scripts/deploy_dashboard.py --cleanup --query-lookback 21d --query-timeout 90
python3 scripts/verify_deployed_dashboards.py --lookback 21d --query-timeout 90 --json docs/health/verify-default-21d-final.json

# Optional legacy extended-data helper
python3 scripts/populate_dashboard_data_14d.py --validate

# Or run individual extended-data steps when debugging
python3 scripts/generate_dashboard_data.py --days 21 --validate
python3 scripts/ingest_test_data.py
python3 scripts/demo_readiness.py --lookback 21d

# Or trigger via the canonical public Control Plane
curl -X POST https://<DEMO_CONTROL_PLANE_HOST>/api/demo-events/trigger \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"preset": "security_incident"}'
```

### Verify Dashboard Data
```bash
python3 scripts/smoke_test_bluelight.py --lookback 24h
python3 scripts/demo_readiness.py --lookback 21d
python3 scripts/query_audit.py --lookback 24h --eligible-only --out /tmp/eligible_query_audit_24h.json
```

### Refresh Dashboards
```bash
python3 scripts/deploy_dashboard.py --cleanup  # Recreate all 29 dashboards after OCI query validation
python3 scripts/generate_catalog.py            # Regenerate catalog
```

---

## Architecture Summary

```
┌──────────────────────────────────────────────────────────────────────┐
│                        OCI-DEMO Platform                             │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │ GOAD AD Lab │  │ Caldera     │  │ OpenAEV     │  │ Kali       │ │
│  │ (8 Windows  │  │ (MITRE      │  │ (Attack     │  │ (HexStrike │ │
│  │  VMs)       │  │  ATT&CK)    │  │  Validation)│  │  Pentesting│ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────┬──────┘ │
│         │                │                │                │        │
│         └────────────────┴────────────────┴────────────────┘        │
│                              │                                       │
│                    ┌─────────▼──────────┐                           │
│                    │  OCI Streaming +   │                           │
│                    │  Service Connector │                           │
│                    │  Hub               │                           │
│                    └─────────┬──────────┘                           │
│                              │                                       │
│              ┌───────────────┼───────────────┐                      │
│              │               │               │                      │
│    ┌─────────▼────┐ ┌───────▼───────┐ ┌─────▼──────┐              │
│    │ OCI Log      │ │ Splunk        │ │ ServiceNow │              │
│    │ Analytics    │ │ (External)    │ │ (Incidents)│              │
│    │ ┌──────────┐ │ └───────────────┘ └────────────┘              │
│    │ │29 SOC    │ │                                                │
│    │ │Dashboards│ │                                                │
│    │ │441 Saved │ │                                                │
│    │ │Searches  │ │                                                │
│    │ │580 Assets│ │                                                │
│    │ │231 MITRE │ │                                                │
│    │ └──────────┘ │                                                │
│    └──────────────┘                                                │
│                                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│  │ CRM Portal  │  │ Drone Shop  │  │ Seven       │                │
│  │ (crm.octo   │  │ (shop.octo  │  │ Kingdoms    │                │
│  │  demo.cloud)│  │  demo.cloud)│  │ Portal      │                │
│  └──────┬──────┘  └──────┬──────┘  └─────────────┘                │
│         │                │                                          │
│         └────────┬───────┘                                          │
│                  │                                                   │
│        ┌─────────▼──────────┐                                       │
│        │ SOC Application    │                                       │
│        │ Logs + OTel-shaped │──▶ Browser Attack Detection           │
│        │ telemetry JSON     │    (XSS, SQLi, CSRF, Fingerprinting) │
│        └────────────────────┘                                       │
│                                                                      │
│  ┌─────────────────────────────────────────────────┐                │
│  │ Control Plane (<DEMO_CONTROL_PLANE_HOST>)               │                │
│  │ ┌───────────┐ ┌──────────┐ ┌─────────────────┐ │                │
│  │ │ One-Click │ │ Stress   │ │ Event Presets   │ │                │
│  │ │ Controls  │ │ Tests    │ │ (P1/P2/P3/P4)   │ │                │
│  │ └───────────┘ └──────────┘ └─────────────────┘ │                │
│  └─────────────────────────────────────────────────┘                │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Detection Coverage Matrix

| Content Surface | Count | Dashboards | What to Emphasize |
|----------------|-------|------------|-------------------|
| Source Sigma/YAML rules | 454 | 14 | Windows, OCI, Linux, web, BLUELIGHT, and browser-side detections |
| Sigma-derived OCI searches | 476 | 14 | 468 top-level detections + 8 browser/app telemetry detections |
| Curated app/APM telemetry analytics | 47 | 3 | App 360 correlation, WAF-to-trace pivots, service health, APM/WAF showcase views, Octo APM spans and metrics |
| Hunting analytics | 95 | 7 | Frequency, anomaly, scoring, multi-stage, kill-chain correlation, MELTS drilldowns |
| STIG-mapped detections | 24 | 1 | Continuous control monitoring for IAM, network, audit, and key management |
| Sample datasets | 17 generated files / 221,078 local events | Demo enablement | Includes app/APM telemetry, network/firewall telemetry, GOAD/Caldera drilldown evidence, the scoped Octo APM workshop dataset, and multicloud geo-health data |
| **Total shipped query artifacts** | **678** | **29** | **231 MITRE techniques across 14 tactics** |

---

## Demo Tips

1. **Set time range to "Last 21 days"** on all dashboards to see the generated demo data (dashboards default to `l21d`)
2. **Use the Ops Portal** for one-click event generation — no SSH needed
3. **Start with Scenario 1** for executive audiences, skip to Scenario 3 for security teams
4. **The BLUELIGHT scenario** is the strongest differentiator — show the SPL→OCL conversion
5. **Browser attack detection** is powered by the custom `SOC Application Logs` telemetry surface, so explain the parser/source model rather than implying native OCI APM coverage
6. **If a dashboard is empty**, regenerate and ingest with `python3 scripts/generate_test_logs.py --days 1 --validate`, `python3 scripts/generate_geo_health_logs.py --duration 60 --interval 5`, and `python3 scripts/ingest_test_data.py --mode direct`
7. **Each query JSON includes** `splunk_original` for Splunk comparison during demos
