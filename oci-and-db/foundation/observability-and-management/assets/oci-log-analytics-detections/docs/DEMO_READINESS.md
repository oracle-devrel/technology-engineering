# Demo Readiness

This is the shortest path to a reliable demo when the goal is broader than security.

## Fast Path

For the current dashboard-first demo state, use the 21-day generation, ingest, deploy, and verify flow:

```bash
python3 scripts/setup_log_sources.py
python3 scripts/generate_dashboard_data.py --days 21 --geo-interval 15 --validate
python3 scripts/ingest_test_data.py --validate
python3 scripts/ingest_test_data.py --mode direct
python3 scripts/deploy_dashboard.py --cleanup --skip-live-validation --query-lookback 21d --query-timeout 90
python3 scripts/verify_deployed_dashboards.py --lookback 21d --query-timeout 90 --max-workers 4 --json docs/health/verify-default-21d-2025-2026.json
```

This is the canonical refresh path because it:

- regenerates the synthetic datasets for a 21-day threat-hunting window
- validates the dataset contracts
- uploads all demo data into OCI Log Analytics
- cleans up and redeploys the dashboards and saved searches
- runs live readiness checks against the same 21-day window
- validates every deployed dashboard saved search in OCI Log Analytics after import

## Current Verified State

Live deployment evidence in the `<OCI_PROFILE_CAP>` OCI profile (`<OCI_REGION>`):

- Local update: `221,078` synthetic events across `17` JSONL datasets generated from `scripts/generate_dashboard_data.py --days 21 --geo-interval 15 --validate` plus the scoped Octo APM workshop generator, including FreeLabFriday vsagent, domain-fronting, port-knocking evidence, the web-to-cloud and Windows AD/GOAD attack sequences, the 2025-2026 MELTS scenarios, and `octo-apm-demo` APM span/metric samples.
- `16/16` standard datasets pass `scripts/ingest_test_data.py --validate`; the scoped Octo APM workshop dataset is optional in the ingest manifest and was uploaded by `deploy_octo_apm_workshop.sh` to `<OCI_PROFILE_CAP>` and `<OCI_PROFILE_EMDEMO>`
- Current repository inventory: `29` dashboards and `441` active dashboard saved searches
- Final live health evidence is stored in `docs/health/all-dashboard-verify.json`
- `<OCI_PROFILE_CAP>`: `441` dashboard widgets deployed, `0` render/query errors (live `parse_validate_all_queries` 681/681 PASS; deploy-time validation 0 failed)
- `DEFAULT`: redeploy and reverify before presenting this profile with the current 22-dashboard inventory
- The Fusion correlation query remains cataloged for Fusion-enabled tenancies but is not deployed in this demo tenancy because no Fusion Apps source exists.
- `scripts/verify_deployed_dashboards.py --lookback 21d --query-timeout 90 --max-workers 4 --json docs/health/verify-<profile>-21d-2025-2026.json` is the current final gate for both `<OCI_PROFILE_CAP>` and `DEFAULT`
- `scripts/setup_log_sources.py`: SOC/native-compatible sources exist in the target compartment; `SOC Application Logs` includes APM span and metric fields used by the Octo dashboard

The current dashboard configuration resolves to `29` dashboards and `441` active saved searches after adding the Octo APM trace investigation Link/Tiles widget. Dashboard widgets default to `l21d` to match the three-week demo dataset; individual widgets may override with a shorter window via query or widget metadata. Use `populate_dashboard_data_14d.py --validate` only when you intentionally need the legacy extended-data helper.

## Demo Story

Lead with three connected views:

1. `SOC: Geographic Health Dashboard`
   Show real multicloud visibility across OCI, Azure, AWS, and GCP.
   Use this as the opening proof that the platform sees all CSPs, not just one telemetry island.

2. `OCI-DEMO: Application 360 Monitoring Dashboard`
   Show performance and availability before security:
   - request rate
   - error rate
   - slow requests
   - service lifecycle timeline
   - DB performance correlation
   - cross-service trace correlation

3. `OCI-DEMO: Octo APM Demo Dashboard`
   Show dedicated APM evidence for `octo-apm-demo`:
   - RED metrics
   - request/error timeline
   - trace-to-log correlation
   - span link analysis
   - metric samples and database spans
   - Java sidecar errors, API Gateway edge decisions, payment threats, OSQuery host evidence, and compromised VM pivots

4. Security correlation views
   Use them as pivots off the performance story, not as the whole demo:
   - `App: WAF Signal Correlation`
   - `App: OWASP Attack Detection`
   - `Browser Attack Detection Dashboard`
   - `C2 & Beaconing Detection`
   - `SOC: FreeLabFriday Threat Hunting Dashboard`
   - `SOC: 2025-2026 Threat Hunting Dashboard`

5. `SOC: Web-to-Cloud Threat Hunting Dashboard`
   Use this as the full incident drilldown:
   - entry request and SSRF evidence
   - compromised machines
   - compromised OCI service identity
   - VCN egress and Network Firewall C2
   - exfiltrated object and destination IP

6. `SOC: 2025-2026 Threat Hunting Dashboard`
   Use this for modern attack drilldowns:
   - MELTS signal overview and timeline
   - ClickFix and CrashFix endpoint execution
   - SharePoint ToolShell web path
   - RMM remote access activity
   - AiTM token replay and exfiltration evidence

## Pre-demo checks

Run these in order:

```bash
python3 scripts/generate_dashboard_data.py --days 21 --geo-interval 15 --validate
python3 scripts/ingest_test_data.py --validate
python3 scripts/deploy_dashboard.py --dry-run
python3 -m unittest discover -s scripts -p 'test_*.py'
```

If you only need a dry check before touching OCI, run:

```bash
python3 scripts/validate_synthetic_logs.py
python3 scripts/deploy_dashboard.py --dry-run
python3 scripts/demo_readiness.py --dry-run
```

After ingest, confirm widget health end-to-end:

```bash
python3 scripts/inventory_dashboards.py
python3 scripts/verify_deployed_dashboards.py --lookback 21d --query-timeout 90
python3 scripts/daily_health_check.py --lookback 21d
```

`daily_health_check.py` chains the inventory + smoke + verifier into one banner with a JSON report under `docs/health/`. Exit codes feed CI gates (0 = OK, 1 = MISS, 2 = ERROR, 3 = auth fail).

## What must be true for tomorrow

- Multicloud health data is present for `OCI`, `Azure`, `AWS`, and `GCP`
- App 360 queries return rows for:
  - throughput
  - error rate
  - slow requests
  - cross-service traces
  - DB correlation
- At least one correlation path is demoable end to end:
  - slow request -> trace correlation -> DB target
  - app request -> WAF signal -> attack source IP
  - degraded region -> provider summary -> unhealthy region detail
  - WAF SSRF -> app host -> VCN egress -> firewall alert -> OCI Audit object read
  - ClickFix -> CrashFix Python RAT -> RMM relay -> VCN/Firewall exfiltration

## Recommended sequence

1. Start with `SOC: Geographic Health Dashboard`
   Message: "We have one operational view across all CSPs."

2. Move to `OCI-DEMO: Application 360 Monitoring Dashboard`
   Message: "We can explain why users are unhappy, not just whether attackers are active."

3. Show `App: Cross-Service Trace Correlation`
   Message: "The same transaction can be followed across services."

4. Show `App: DB Performance Correlation`
   Message: "Database context is tied back to application traces and logs."

5. Move to `OCI-DEMO: Octo APM Demo Dashboard`
   Message: "The Octo APM view correlates logs, APM-shaped spans, and metrics through shared trace and span fields."

6. Show `App: WAF Signal Correlation`
   Message: "Security is part of the same operational story, not a separate console."

6. Show `SOC: Web-to-Cloud Threat Hunting Dashboard`
   Message: "Now we can follow one incident end to end from web entry to cloud data exfiltration."

7. Show `SOC: FreeLabFriday Threat Hunting Dashboard`
   Message: "The same analytics surface can pivot through source-attributed training scenarios: DNS C2, BITS/cloud exfiltration, domain-fronted C2, vsagent beaconing, credential stuffing, rogue user creation, and port knocking."

8. Show `SOC: 2025-2026 Threat Hunting Dashboard`
   Message: "Modern attack hunting starts with MELTS correlation, then drills into ClickFix, CrashFix, ToolShell, RMM, token replay, compromised machines, and exfiltrated data."

## Hard limit

Synthetic datasets now pass explicit schema contracts and the 21-day dashboard verification path in OCI. Perfect fidelity to every real tenant log format still requires captured raw samples from the target OCI, Azure, AWS, and GCP environments. Use `scripts/validate_synthetic_logs.py` and the live OCI audits as confidence checks, not as proof of 100 percent production parity.
