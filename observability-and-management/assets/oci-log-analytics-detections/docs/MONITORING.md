# SOC Detection Monitoring

Operator playbook for keeping the deployed SOC dashboards green over time.
The monitoring stack is built from four scripts under `scripts/` plus a
single wrapper that ties them together.

For OKE cluster telemetry, OCI Kubernetes Monitoring, and Forge-on-OKE rollout
checks, use [OKE_OBSERVABILITY_RUNBOOK.md](OKE_OBSERVABILITY_RUNBOOK.md). That
runbook covers the reusable `Latest telemetry: Unknown` / `Invalid Date`
diagnostic, ONM discovery validation, OCI Monitoring metric checks, and
cross-architecture container build guidance.

## Daily health check

Run `scripts/daily_health_check.py` once a day (manually or scheduled).
The wrapper executes the full pre-flight cycle and emits one banner plus a
JSON report under `docs/health/`:

```bash
python3 scripts/daily_health_check.py --lookback 21d
```

Sections:

1. **Inventory** — `scripts/inventory_dashboards.py` lists every Management
   Dashboard in the compartment, classifies SOC vs other, and reports
   missing / duplicate / legacy / broken instances.
2. **BLUELIGHT smoke** — `scripts/smoke_test_bluelight.py` runs the 17
   per-stage detections plus the kill-chain hunt against live OCI Log
   Analytics. Demo-critical baseline; expected `17/17 HIT`.
3. **Per-widget verifier** — `scripts/verify_deployed_dashboards.py`
   fetches every deployed dashboard, runs the actually-stored
   `queryString` from each embedded saved search, reports per-dashboard
   HIT/MISS/ERROR, and flags widget-count mismatches.

Exit codes feed CI gates:

| Code | Meaning                                            |
|------|----------------------------------------------------|
| 0    | All dashboards present, every query returning rows |
| 1    | At least one widget MISS (zero rows) but no errors |
| 2    | At least one ERROR or missing/mismatched dashboard |
| 3    | OCI auth / namespace lookup failed                 |

## Operational scripts

| Script                                | Purpose                                              | Lookback default |
|---------------------------------------|------------------------------------------------------|------------------|
| `inventory_dashboards.py`             | Census + classification of dashboards                | n/a              |
| `cleanup_soc_dashboards.py`           | Delete SOC dashboards + saved searches by prefix     | n/a              |
| `smoke_test_bluelight.py`             | 17 BLUELIGHT detections + kill-chain hunt            | `30d`            |
| `smoke_test_all_queries.py`           | Walk every `queries/**.json` and run filter half     | `21d`            |
| `verify_deployed_dashboards.py`       | Fetch each deployed dashboard, run stored queries    | `21d`            |
| `daily_health_check.py`               | Wraps the three above, emits banner + JSON report    | `21d`            |

All scripts honor `--lookback Nd|Nh|Nm` and (where applicable) `--json` for
machine-readable output.

## Cleanup → redeploy round-trip

When dashboards drift (titles change, widgets become orphaned, parsers
update):

```bash
python3 scripts/cleanup_soc_dashboards.py --dry-run   # confirm scope
python3 scripts/cleanup_soc_dashboards.py             # execute
python3 scripts/deploy_dashboard.py                   # redeploy
python3 scripts/verify_deployed_dashboards.py --lookback 21d --query-timeout 90
```

Note: redeploy can take **20–30 minutes** end-to-end because OCI
Management Dashboard API throttles `create_management_saved_search` calls
between 100 and 140. Cleanup is fast (<30 s).

For surgical query patches on already-deployed widgets, use
`update_management_saved_search` directly — see the snippet in
`scripts/smoke_test_bluelight.py` history (commit `d9e459b`) for an
example that ran 5–10× faster than a full redeploy.

## Cloud Guard data path note

Detection queries on the SOC Cloud Guard Security Dashboard target three
candidate sources via OR:

```
'Log Source' = 'OCI Cloud Guard Problems'
            OR 'OCI Cloud Guard Logs'
            OR 'SOC Cloud Guard Logs'
```

The native `OCI Cloud Guard Problems` parser does not extract
`problemName` from the JSON envelope into the `Problem Name` field that
detections reference. The SOC `socCloudGuardJsonParser` registered by
`scripts/setup_log_sources.py:CG_FIELD_MAPPINGS` does (`$.problemName` →
`Problem Name`).

Therefore `cloud_guard.jsonl` must land in **SOC Cloud Guard Logs**, not
the native source. `oci_config.SOURCE_CANDIDATE_GROUPS["cloud_guard"]`
puts SOC first explicitly so the upload resolver picks the right
destination. If you ever re-add the native source first, the
`SOC: Cloud Guard Security Dashboard` widgets will silently MISS.

## JSON report layout

`docs/health/health-<timestamp>.json`:

```json
{
  "timestamp": "2026-04-28T22:00:00Z",
  "lookback": "21d",
  "overall_status": "OK | MISS | ERROR",
  "sections": [
    {"name": "inventory",        "exit_code": 0, "output": "..."},
    {"name": "bluelight_smoke",  "exit_code": 0, "output": "..."},
    {"name": "verifier",         "exit_code": 0, "output": "..."}
  ]
}
```

Companion artifacts the wrapper writes alongside (also gitignored):

- `inventory-<timestamp>.json` — dashboard census output
- `verify-<timestamp>.json`    — per-widget HIT/MISS/ERROR records

## Scheduling

The simplest cron line:

```cron
# Daily 06:00 UTC — generate report, ignore non-zero exit
0 6 * * * cd /path/to/oci-log-analytics-detections && \
  /usr/bin/env python3 scripts/daily_health_check.py --lookback 21d \
  >> /var/log/soc-health.log 2>&1
```

For an interactive Claude Code session, the equivalent is `/schedule`
with a one-off or recurring agent that runs `daily_health_check.py`,
reads the resulting JSON report, and pastes the banner back into the
session.
