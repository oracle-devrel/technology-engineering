# OCI Log Analytics Detection Rules Enhancement Plan

## Goal
Enhance the OCI Log Analytics project by creating a comprehensive library of detection rules (starting with 100+) inspired by industry standards (Sigma, Elastic, Splunk) and tailored for OCI. The project will include automated tooling to convert Sigma-format rules into OCI Log Analytics Query Language (OCL).

## Phase 1: Foundation & Setup ✅
- [x] **Project Structure:** Initialize directories for rules, queries, scripts, and config.
- [x] **Metadata Definition:** Define the schema for tracking rule status, fields, and sources.
- [x] **Mapping Configuration:** Create `sigma_oci_mapping.yaml` to map Sigma fields to OCI Log Analytics fields.

## Phase 2: Tooling (The "Converter") ✅
- [x] **Advanced Scripting:** `scripts/convert_sigma.py` supports advanced logic (NOT, AND/OR, startswith, endswith).
- [x] **Field Modifiers:** Support for `|contains`, `|startswith`, `|endswith`.
- [ ] **Validation:** Implement automated validation of generated OCL syntax.

## Phase 3: Content Creation (First 100 Rules) ✅
- [x] **OCI Specific Rules:** Implemented audit events for IAM, Network, and Compute.
- [x] **Cloud Guard Integration:** Rules for Cloud Guard problem detection.
- [x] **OS Level Rules:** Linux suspicious binaries and Windows LOLBins.
- [x] **Continuous Expansion:** Surpassed 200 source rules and continued expansion through SigmaHQ adaptation and custom content.

## Phase 4: Dashboard & Visualization ✅
- [x] **Dashboard Scripting:** `scripts/generate_dashboard_config.py` created.
- [x] **OCI Deployment Tool:** `scripts/deploy_dashboard.py` fully functional.
- [x] **Test Data:** `scripts/ingest_test_data.py` created for simulation.
- [x] **Dashboard Completion:** Successfully deployed the SOC Security Dashboard with 6 core widgets.

## Phase 5: OCI Log Analytics Deployment ✅
- [x] **Log Source Mapping Fix:** Corrected Cloud Guard, Linux, and Windows log source mappings.
- [x] **UUID Fix:** Replaced all placeholder UUIDs with proper UUIDs.
- [x] **Query Regeneration:** Generated query inventory expanded far beyond the initial 113-query milestone.
- [x] **Saved Searches:** Deployment pipeline matured from the initial 58 saved searches to the current 326-saved-search, 21-dashboard content set documented in the repo.
- [x] **Dashboards:** 21 dashboards deployed across SOC overview, OCI audit/STIG, Cloud Guard, Linux, Windows, GOAD/AD, C2, FreeLabFriday, 2025-2026 MELTS, web, web-to-cloud, app, geographic health, APT, and browser telemetry views.
- [x] **Test Data Pipeline:** 257,754 NDJSON events generated across 16 files and uploaded to both `cap` and `DEFAULT`.
- [x] **Dashboard Widget Fix:** Rewrote saved searches with proper `ui_config`/`scopeFilters` format and embedded in dashboard JSON for `import_dashboard` API.
- [x] **Documentation:** Updated README.md, STATUS.md, PLAN.md.

## Phase 6: Advanced Features & Automation ✅
- [x] **Remote Rule Sync:** `scripts/sync_sigmahq.py` fetches rules from SigmaHQ repository.
- [x] **Rule Catalog:** `scripts/generate_catalog.py` generates CATALOG.md and catalog.json.
- [x] **CI/CD Integration:** `.github/workflows/validate-rules.yml` validates on push/PR.

## Phase 8: OCI Resource Manager Stack ✅
- [x] **Terraform Stack:** Full ORM-compatible stack in `stack/` directory for one-click deployment.
- [x] **ORM Schema:** `schema.yaml` renders variable form UI in OCI Console (compartment picker, toggles for log sources/dashboards/test data).
- [x] **Infrastructure as Code:** Log Analytics log group, 4 streams, 4 SCH connectors, IAM policies — all managed declaratively.
- [x] **Python Provisioners:** `null_resource` blocks call existing scripts (`setup_log_sources.py`, `deploy_dashboard.py`, `ingest_test_data.py`) with proper dependency ordering.
- [x] **Build Script:** `build_stack.sh` produces `soc-detection-stack.zip` ready for ORM upload.
- [x] **Validation:** `terraform init` + `terraform validate` pass cleanly.

## Rule Organization
- **Format:** Sigma (YAML) as the source of truth.
- **Output:** OCL queries (JSON format).
- **Structure:**
    ```
    rules/
      cloud/
        oci/
          audit_events/
          cloud_guard/
        aws/
        gcp/
      linux/
        suspicious_binaries/
      windows/
        process_creation/
    ```

## Phase 7: STIG Compliance & Advanced Attack Patterns
- [x] **OCI STIG Rules:** 15 new rules with STIG control mappings (IA-2, SC-7, AU-11, etc.)
- [x] **Advanced Linux Rules:** Container escape, LD_PRELOAD hijack, kernel module from /tmp, passwd modification, ptrace injection, network redirect.
- [x] **Advanced Windows Rules:** Shadow copy deletion (ransomware), AMSI bypass, WMI persistence, registry run key, DLL side-loading, bcdedit recovery disable.
- [x] **Enhanced Converter:** List support for startswith/endswith, STIG metadata, condition tokenizer, validation and stats modes.
- [x] **STIG Compliance Dashboard:** New dedicated dashboard with 14 compliance widgets.
- [x] **Test Data Expansion:** 360 events (up from 279) covering all 140 rules.
- [x] **Multicloud Integration:** Export script for ~/dev/multicloudoperations with shared manifest.

## Phase 9: Canonical Inventory Reconciliation ✅
- [x] **Canonical Source Rule Count:** Verified 454 YAML rules on disk.
- [x] **Canonical Generated Query Count:** Verified 446 base detection queries, 40 hunting queries, and 20 app/APM queries.
- [x] **Documentation Reconciliation:** Updated README/PLAN to distinguish source rules from generated query assets.
- [x] **Catalog Contract Hardening:** Extended `queries/catalog.json` generation with inventory metadata for downstream consumers.

## Success Criteria
1.  100+ high-quality detection rules implemented. (Achieved: 454 source YAML rules)
2.  Functional conversion script from Sigma to OCL. (Achieved: Advanced version with STIG metadata and catalog generation)
3.  Comprehensive documentation. (Achieved, with canonical inventory reconciled to disk state)
4.  Functional SOC Dashboards in OCI. (Achieved: 21 dashboards and 326 active saved searches deployed as the current 2025-2026 threat-hunting content set)
5.  STIG compliance mapping for OCI rules. (Achieved: 24 generated detection queries carry STIG mappings, spanning 12 controls)
6.  Cross-project integration with multicloudoperations. (Achieved: export script + manifest + canonical CSP schema builders ported to `scripts/schemas/`)
7.  One-click deployment via OCI Resource Manager. (Achieved: Terraform stack with ORM schema)
8.  Live dashboard health verifier. (Achieved: `scripts/verify_deployed_dashboards.py` runs every embedded saved search against live OCI LA; `scripts/daily_health_check.py` chains the inventory + smoke + verifier with JSON report under `docs/health/`)

## Phase 10: Canonical CSP Schema Builders (2026-04-28) ✅

- [x] **Schema Module Port:** Brought `oci_audit_schema`, `windows_audit_schema`, `azure_audit_schema`, `gcp_audit_schema` from `multicloudoperations/shared/` into `scripts/schemas/`.
- [x] **Refactor Generators:** `oci_audit_event`, `winsec_event`, `sysmon_op_event` now delegate to the canonical builders so synthetic logs match real CSP envelopes verified against live API output.
- [x] **Schema Fidelity Tests:** Ported 4 schema fidelity test modules; pinned 35 new tests against the real CloudEvents v0.1, EVTX, Azure Monitor, and GCP LogEntry shapes.
- [x] **Dual-Keyed Records:** Every record carries native CSP envelope at top level + parallel OCI LA display-name columns so detection queries match through either path.

## Phase 11: Operational Toolkit and Health Loop (2026-04-28 → 2026-05-04) ✅

- [x] **Inventory Tool:** `scripts/inventory_dashboards.py` — census + classification of dashboards, flags missing/duplicate/legacy/broken instances.
- [x] **Cleanup Tool:** `scripts/cleanup_soc_dashboards.py` — aggressive deletion of SOC dashboards + saved searches by name prefix (catches drift from prior iterations).
- [x] **Smoke Test (Targeted):** `scripts/smoke_test_bluelight.py` — 17 BLUELIGHT widgets + kill-chain hunt against live OCI LA.
- [x] **Smoke Test (Full):** `scripts/smoke_test_all_queries.py` — walks every `queries/**.json` and runs the raw filter half against live OCI LA.
- [x] **Verifier:** `scripts/verify_deployed_dashboards.py` — fetches every deployed dashboard, runs the actually-stored saved-search `queryString` against live OCI LA, reports per-dashboard HIT/MISS/ERROR.
- [x] **Daily Wrapper:** `scripts/daily_health_check.py` — chains inventory + smoke + verifier with JSON report under `docs/health/`.
- [x] **Cloud Guard Routing Fix:** Reordered `SOURCE_CANDIDATE_GROUPS["cloud_guard"]` so test data lands in `SOC Cloud Guard Logs` whose parser extracts `Problem Name`. Closed all 12 Cloud Guard widget MISSes.
- [x] **Linux Crontab Routing Fix:** Reordered `SOURCE_CANDIDATE_GROUPS["linux_secure"]` so test data lands in `SOC Linux Syslog Logs` whose parser extracts `Command Line`.
- [x] **OCI Status Dual-Form:** Source rules now use Sigma list syntax `status: [Success, '200']` so detections match both operator-friendly and HTTP-code parser projections.
- [x] **OCI LA SEARCH-LIKE Caveats:** Documented in `docs/ARCHITECTURE.md` — String-typed field quoting, multi-word LIKE wildcard tokenisation, `Original Log Content` truncation window, parser projection vs filter divergence.
- [x] **Monitoring Runbook:** `docs/MONITORING.md` — daily check, cleanup → redeploy round-trip, Cloud Guard data-path note, sample cron line.
- [x] **Codex Stop-Time Review Gate:** Enabled via `node …/codex-companion.mjs setup --json --enable-review-gate` so every stop runs an independent code review.

## Phase 12: Forward Roadmap (Next 4–6 Weeks)

Sorted by impact / cost ratio.

### 12.1 Sigma converter — backslash escape fix (1–2 days)

**Problem.** `convert_sigma.py` emits LAQL like `'Pipe Name' = '\interprocess_'` (one literal backslash) for Windows pipe-name rules. OCI LA's SEARCH parser rejects this with `Unexpected input for SEARCH: '\interprocess_'`. Affected detection queries (Cobalt Strike, Mimikatz pipes) currently exist as hand-edited files that must not be regenerated.

**Plan.**
- [x] Add a backslash-doubling pass in `scripts/convert_sigma.py` for any value containing literal `\` so the generated LAQL has properly-escaped patterns.
- [x] Add a fallback wildcard heuristic for `Pipe Name` rules: `*pattern*` rather than exact-match.
- [x] Add a `do_not_overwrite: true` rule annotation respected by the converter so hand-edited query files are protected even when their YAML source runs through a regeneration sweep.
- [ ] Regenerate all queries cleanly and re-verify with `verify_deployed_dashboards.py` to confirm no widget regresses.

### 12.2 Dual-Status audit guardrail

- [x] Audit every `rules/cloud/oci/*.yaml` rule that filters on successful status.
- [x] Confirm current successful-status selectors use list form `status: [Success, '200']` so detections survive both SOC custom and native OCI Audit parser projections.
- [x] Add a regression test that fails if a future OCI Audit rule reintroduces a Success-only selector.

### 12.3 Close current live widget misses

Current deployed target is **326 active dashboard widgets** across `21` dashboards in both `cap` and `DEFAULT` `eu-frankfurt-1` demo tenancies using the 21-day dataset.

`Hunt: OCI IAM + Fusion Correlation` needs `Fusion Apps: Sign In - Sign Out Activity Logs` and `Fusion Apps: ESS Audit Logs` log sources. Two options:

- [ ] **Option A:** add a Fusion Apps test-data emitter + parser, ingest, and verify the correlation widget HITs.
- [x] **Option B:** keep the Fusion correlation query cataloged under `queries/hunting/` but out of the active dashboard set for tenancies that do not run Fusion. The active dashboard set now includes the C2, FreeLabFriday, 2025-2026 MELTS, browser, APT, app, GOAD/AD, and web-to-cloud dashboard additions.

`DNS: Data Exfiltration` needed refreshed Sysmon Operational DNS query data in the live tenancy:

- [x] Add deterministic long `Query Name` values to `generate_sysmon_operational()` for the widget's `domain_length > 30` predicate.
- [x] Ingest refreshed `test_data/sysmon_operational.jsonl` through `scripts/ingest_test_data.py --mode direct`.
- [x] Rerun `scripts/verify_deployed_dashboards.py --lookback 21d --query-timeout 90 --json docs/health/verify-<profile>-21d-final.json` and confirm the widget remains HIT.

### 12.4 Web-to-cloud incident drilldown (2026-05-04)

- [x] Add `SOC: Web-to-Cloud Threat Hunting Dashboard` with 10 widgets.
- [x] Add curated hunting queries for entry point, compromised machines, compromised identity, VCN egress, Network Firewall C2, cloud abuse, exfiltration, link analysis, and stage breakdown.
- [x] Add OCI-shaped `vcn_flow.jsonl` and `network_firewall.jsonl` datasets plus parser/source routing.
- [x] Generate 21-day local data across 16 JSONL files.
- [x] Run live log-source setup, direct ingest, dashboard cleanup deploy, and `verify_deployed_dashboards.py --lookback 21d --query-timeout 90` in both `cap` and `DEFAULT`.

### 12.5 Legacy C2 dashboard refresh (2026-05-05) ✅

- [x] Replace the legacy `C2 & Beaconing Detection` dashboard with current Sysmon DNS/network, VCN Flow, and Network Firewall queries.
- [x] Add 10 C2 widgets covering DNS beacon domains, source processes, affected hosts, flow counts, destination IPs, HTTPS callbacks, timeline, and link topology.
- [x] Add targeted dashboard deploy and verify support with `--dashboard-name` so old dashboards can be refreshed without broad cleanup.
- [x] Verify the refreshed C2 dashboard in both the legacy parent compartment and the main `demo-observability` compartment.

### 12.6 Schedule the daily health check (1 hour)

- [ ] Add a recurring routine that runs `scripts/daily_health_check.py --lookback 21d` on a weekly cadence.
- [ ] Diff the JSON report against the previous run; surface widget regressions before deploy.
- [ ] Optionally publish the banner to a Slack channel via `slack:draft-announcement` skill.

### 12.7 Sigma converter — `condition` operator coverage (3–5 days)

Minor backlog from earlier phases:

- [ ] Implement automated validation of generated OCL syntax (Phase 2 leftover).
- [ ] Audit converter coverage for advanced Sigma `condition` operators: `1 of`, `all of`, `near`, count modifiers.
- [ ] Add a per-rule `--validate` mode that round-trips the generated query through OCI LA syntax check.

### 12.7 Field dictionary — `DET-MISS-002` (2 days)

- [ ] Generate a machine-readable log-source field dictionary from `scripts/setup_log_sources.py:*_FIELD_MAPPINGS` so downstream UIs (LoganSecurityDashboardv0) know which display names exist on which sources.
- [ ] Cross-reference each detection query's field dependencies against the dictionary; flag queries that reference unmapped fields before deploy.

### 12.8 Test-data schema validation hardening (3 days)

- [x] Add `scripts/validate_synthetic_logs.py` checks for every `test_data/*.jsonl` against `config/synthetic_log_contracts.json`.
- [ ] Run the validator inside CI so generator drift breaks the build.
- [ ] Pin schema version with the same `do_not_overwrite` discipline as the canonical schema builders in `scripts/schemas/`.

### 12.9 Atomic Red Team mapping coverage

- [x] Fill missing `atomic_red_team` fields for testable Windows/Linux query artifacts.
- [x] Add `scripts/map_atomic_tests.py --enrich --missing-only` so future gap-fills do not rewrite existing ART mappings.
- [x] Regenerate `docs/ART_COVERAGE_REPORT.md` after the current mapping pass.
- [ ] Decide whether the 9 unmapped testable rules should remain documented no-match cases or receive custom validation notes.

### 12.10 Expand live verification beyond Caldera discovery (2 weeks)

- [ ] Caldera operations covering: credential-access, lateral-movement, collection, and exfiltration.
- [ ] Per-operation verification queries layered on `scripts/verify_caldera_detections.py`.
- [ ] Demo data deterministic enough that `daily_health_check.py` confirms each kill-chain stage independently.
