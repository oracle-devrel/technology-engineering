# Project Status

Date: 2026-05-18

## Current State

- Core scope: OCI Log Analytics query generation, synthetic log generation, query/dashboard validation, OCI dashboard creation, and the integrated Forge conversion webapp.
- Source Sigma/YAML rules: 522
- Sigma-derived OCI query artifacts: 553
  - 545 top-level detections in `queries/`
  - 8 browser/app telemetry detections in `queries/apps/`
- Microsoft Sentinel converted queries: 60 live OCI parser-passing queries
- Curated analytics: 169
  - 54 app telemetry analytics
  - 115 hunting analytics
- Total query artifacts/content items: 782
- MITRE ATT&CK coverage: 243 techniques across 14 tactics
- MITRE ATLAS (AI/ML) coverage: 10 techniques across 10 tactics on `SOC Application Logs` + the `SOC GenAI Gateway Logs` source
- Dashboards: 29
- Saved searches: 441 active dashboard saved searches; 782 total content items
- Sentinel live validation: 60 / 62 locally clean conversions; 2 live failures remain in `queries/sentinel_conversion_report.json`
- Sentinel synthetic live-hit check: **20 / 20 ready Logan QL queries HIT** in the `cap` profile with a 24-hour lookback after uploading Sentinel-shaped synthetic logs.
- Latest full live dashboard deployment: **441 widgets across 29 dashboards** in the `cap` profile with a 21-day lookback — 0 render/query errors; live `parse_validate_all_queries` 681/681 PASS.
- Generated demo data: 20 NDJSON files / 221,173 events in the latest local `test_data/manifest.json`
- MITRE ATT&CK coverage: 243 techniques / 14 tactics
- STIG coverage: 24 detections / 12 controls
- Atomic Red Team coverage: 280 / 397 testable rules have mapped tests

## Architecture Updates Shipped

- `rules/**` is now explicitly documented as the source authoring layer.
- `queries/catalog.json` is treated as the canonical machine-readable inventory.
- `queries/manifest.json` is treated as an export/integration artifact instead of the canonical inventory.
- Sigma-derived browser detections under `rules/web/browser_attacks/` publish into `queries/apps/`.
- Generated query paths are stabilized by `sigma_id`, which avoids filename churn when titles change.
- Catalog generation, rule quality auditing, and multicloud export now walk the full `queries/**` tree instead of assuming everything lives at the top level.
- Browser/app dashboards now run on `SOC Application Logs`, a custom JSON source that carries OpenTelemetry-shaped fields into OCI Log Analytics.
- Browser attack dashboards now include APM/WAF showcase widgets for attack volume, OWASP breakdown, trace correlation, and cross-tier WAF correlation.
- `queries/dashboard_inventory.json` is generated from `scripts/deploy_dashboard.py:DASHBOARDS` and is the dashboard-facing saved-search/widget inventory.
- Dashboard deployment now validates the generated inventory locally and validates every unique dashboard query in OCI Log Analytics before importing dashboards or embedded saved searches.
- Live query validation runs each query in an isolated child process so slow or hung queries become blocking validation failures instead of reaching dashboard import.
- Dashboard saved-search widgets now default to `l21d`, matching the generated three-week security dataset; the full demo deploy path passes `--query-lookback 21d` for deploy-time OCI query validation.
- Dashboard contract tests now block unsupported live-validation query patterns such as `regexextract`, `countif`, `case`, unmapped Windows fields, and regex-match expressions before OCI import.
- BLUELIGHT (S0657 / APT37) APT dashboard now leads with 5 showcase widgets (Total Detections KPI tile, Top Affected Hosts summary, MITRE Tactics × Techniques summary table, Kill Chain Timeline line chart, Attack Path link analysis) followed by the 17 per-stage detection widgets, presenting the full attack chain on a single canvas.
- WAF parser now extracts `Trace ID` so APM browser attacks correlate to upstream WAF blocks across `SOC Application Logs` and `SOC WAF Security Logs` via shared `traceId`.
- BLUELIGHT kill-chain test data is mirrored into both `windows_sysmon.jsonl` (SOC Windows Sysmon parser, 35 field maps) and `sysmon_operational.jsonl` (Sysmon Operational parser) so per-widget detections match through whichever parser route propagates first.
- All BLUELIGHT queries standardised on quoted `'Event ID' = 'N'` form — OCI LA returns HTTP 400 on unquoted numeric comparisons against String-typed fields, so the convention applies repo-wide for parser-string fields.
- `scripts/smoke_test_bluelight.py` — live OCI LA query runner reports HIT/MISS/ERROR per widget with row counts, used as the green-light gate before deploys.
- Synthetic OCI audit logs now expose operator-friendly `Status` labels and policy keywords needed by dashboard searches; Windows, Sysmon, Linux, and WAF datasets now include rare processes, named-pipe IOCs, DNS tunneling tools, Linux command lines, CORS attacks, and allowed SQLi cases so matching widgets populate from generated data.
- Source-resolver routing for `linux_secure.jsonl` and `cloud_guard.jsonl` now puts SOC custom log sources first so the SOC parsers (which extract `Command Line`, `Problem Name`, etc.) win over the native parsers (which surface a narrower field set). Documented in `docs/MONITORING.md` so future contributors do not reverse the order.
- OCI Audit detection rules that filter on `status: Success` now use Sigma list syntax `status: [Success, '200']` to match both operator-friendly Status labels and the native parser's HTTP-code projection (`com.oraclecloud.computeapi.terminateinstance`, `com.oraclecloud.consolesignon.login`).
- LIKE-on-multi-word phrases use `*token1*token2*` wildcard form repo-wide because OCI LA's SEARCH operator tokenises on whitespace inside LIKE patterns. The `OCI: Admin Policy - Manage All` widget query is the canonical example.
- `daily_health_check.py` chains `inventory_dashboards.py`, `smoke_test_bluelight.py`, and `verify_deployed_dashboards.py` into a single banner with a JSON report under `docs/health/`. Exit codes feed CI gates.
- Stop-time review gate is enabled for this repository — Codex reviews every change before stop. Toggle via `node …/codex-companion.mjs setup --json --enable-review-gate`.
- `test_data/manifest.json` is rebuilt from generated `*.jsonl` files rather than hand-maintained counts.
- Streaming pipeline reconciliation refreshes `config/streaming_config.json` against the active tenancy resources.
- `webapp/` is now the maintained Forge UI in this repository; it consumes generated artifacts and links to `https://github.com/adibirzu/oci-log-analytics-detections`.

## Branch and Worktree State

- Only `main`, `origin/main`, and `origin/HEAD -> origin/main` are present after `git fetch --all --prune`.
- The worktree was clean at the start of the 2026-05-03 scope cleanup pass.
- Optional runtime helpers remain in the repository for Log Analytics ingestion support, but the canonical surfaces are `rules/**`, `queries/**`, generated manifests, synthetic logs, dashboard deployment scripts, and `webapp/`.

## Quality and Verification

Live and local verification on 2026-06-09 (eu-frankfurt-1 tenancy):

- `python3 scripts/deploy_dashboard.py --query-lookback 21d`
  - 29 / 29 dashboards present, 0 missing, 0 widget-count mismatches
  - **441 widgets deployed, 0 ERROR** — deploy-time validation passed 410/410 unique queries (42 empty/no-match in window). The Fusion correlation query `hunting/oci_iam_fusion_activity_correlation.json` is cataloged but not deployed (no Fusion Apps source in this tenancy).
- `python3 scripts/smoke_test_bluelight.py --lookback 21d`
  - 17 / 17 BLUELIGHT detection widgets HIT
- `python3 scripts/daily_health_check.py --lookback 14d`
  - inventory + smoke + verifier banner, JSON report written to `docs/health/health-<timestamp>.json`
- `python3 -m pytest -q`: 129 passed, 5 skipped
- `python3 -m compileall -q scripts`: passed

Local scope-cleanup verification on 2026-05-03:

- `python3 -m pytest -q`: 129 passed, 5 skipped
- `python3 -m compileall -q scripts`: passed
- `python3 scripts/generate_test_logs.py --days 1 --validate`: 2,922 events across 14 files; 547 query files counted across query surfaces
- `python3 scripts/deploy_dashboard.py --validate`: 547 query files OK

Previous local and pre-flight verification on 2026-04-28 before the current catalog expansion:

- `python3 scripts/audit_rule_quality.py --report docs/RULE_QUALITY_REPORT.md`
  - 454 rules / 454 source-derived queries / 0 issues
- `python3 -m pytest -q`
  - 483 tests passed
- `python3 -m compileall scripts`
  - passed
- `python3 scripts/deploy_dashboard.py --validate`
  - OCID, CLI profile, namespace, compartment, and 681 query files passed
- `python3 scripts/deploy_dashboard.py --dry-run`
  - 29 dashboards / 441 saved searches resolved from generated inventory
- `python3 scripts/deploy_dashboard.py --cleanup`
  - 410/410 unique dashboard queries validated in OCI Log Analytics with a 21-day lookback
  - 42 validated query files returned no rows in that window
  - 29 dashboards imported with 441 embedded saved searches
- `python3 scripts/generate_test_logs.py --days 1 --validate`
  - 1,541 core security/app events generated and 681 query files counted across all query surfaces
- `python3 scripts/generate_geo_health_logs.py --duration 60 --interval 5`
  - 1,296 multicloud health events generated
- `python3 scripts/ingest_test_data.py --validate`
  - 14 datasets and log source mappings passed
- Targeted live OCI validation:
  - `python3 scripts/smoke_test_bluelight.py --lookback 24h`: 17/17 BLUELIGHT detection widgets HIT
  - Dashboard listing check: 29/29 dashboard display names found once after deploy import

Previously live-verified on 2026-04-28 (eu-frankfurt-1):

- `python3 scripts/smoke_test_bluelight.py --lookback 24h`
  - 17/17 BLUELIGHT detection widgets HIT
  - 5/5 BLUELIGHT showcase widgets HIT
  - 13/13 APM browser-attack widgets HIT including cross-tier WAF correlation
- `python3 scripts/setup_log_sources.py`
  - 13 parsers OK
- `python3 scripts/ingest_test_data.py --mode direct`
  - 14/14 uploads completed

Previously live-verified on 2026-04-15:

- `python3 scripts/setup_log_sources.py`
  - succeeded
  - all parsers mapped cleanly, including `Logon ID` and `Integrity Level`
- `python3 scripts/setup_streaming_pipeline.py`
  - rewrote `config/streaming_config.json` for the active compartment/log group
  - 5 SOC connectors active
- `python3 scripts/validate_pipeline.py --e2e`
  - all checks passed
  - end-to-end publish and delivery verified through Log Analytics
- `python3 scripts/verify_caldera_detections.py --operation discovery --lookback 60d`
  - 3/3 discovery verification queries matched
- `python3 scripts/export_for_multicloud.py --manifest-only`
  - 454 Sigma-derived queries exported

## Current Runtime Notes

- `validate_pipeline.py` now derives expected streams/connectors from `config/streaming_config.json`, so the multicloud-health connector is validated alongside the core SOC pipeline.
- Redundant active connectors were removed from the compartment without affecting the SOC streaming path.
- `test_data/manifest.json` is current as of 2026-05-03 and reports 2,922 generated local events. `test_data/` is ignored by git and should be regenerated before a fresh ingest.

## Documentation Map

- `README.md` — public overview, quickstart, deployment, and dashboard inventory
- `docs/ARCHITECTURE.md` — source/generation/deployment architecture
- `docs/WEBAPP.md` — integrated Forge webapp contract, security posture, and deployment notes
- `CATALOG.md` — human-readable content catalog
- `queries/catalog.json` — canonical machine-readable inventory
- `queries/dashboard_inventory.json` — dashboard/widget/saved-search inventory for webapp and downstream integrations
- `docs/INTEGRATION_SCHEMA.md` — generated artifact contract for downstream integrations
- `docs/DEMO_WORKFLOW.md` — demo/operator walkthrough
- `docs/RULE_QUALITY_REPORT.md` — latest quality audit output
- `CONTRIBUTING.md` — contributor workflow and validation expectations

## Catalog-Only Queries

The following queries are included in `queries/catalog.json` as reference analytics
but are **not wired into any deployed dashboard** in `scripts/deploy_dashboard.py`
and do not appear in `queries/dashboard_inventory.json`.  They are available for
manual saved-search creation or future dashboard inclusion once the required data
sources are provisioned.

| Query file | Reason for catalog-only status |
|---|---|
| `queries/hunting/oci_iam_fusion_activity_correlation.json` | Requires `Fusion Apps: Sign In - Sign Out Activity Logs` and `Fusion Apps: ESS Audit Logs` sources, which are not provisioned in the demo tenancy.  Verified absent from `scripts/deploy_dashboard.py` (grep clean) and `queries/dashboard_inventory.json`. The single dashboard MISS noted in the 2026-05-04 verification run (`Hunt: OCI IAM + Fusion Correlation`) was from an earlier deploy cycle; the widget has since been removed from the deployed dashboard set. |

## Recommended Next Work

See `PLAN.md` for the prioritised forward roadmap. High-level themes:

1. **Sigma converter quality** — DONE. `convert_sigma.py` doubles literal backslashes in string/`LIKE` selectors and rewrites exact `PipeName` matches into escaped wildcard `LIKE` patterns, and also honors a `do_not_overwrite: true` annotation (rule source or on-disk JSON). Regenerating the 4 `rules/windows/pipe_created/*.yaml` (Cobalt Strike / Mimikatz / PsExec / generic C2) produces validator-clean LAQL with no half-escaped backslashes. Regression-fenced by `scripts/test_pipe_escaping.py` (modifier + exact escaping, end-to-end per-rule structural validation, and `do_not_overwrite` preservation); the per-query validator logic is now reusable via `convert_sigma.query_syntax_issues()`.
2. **Sweep the dual-Status pattern** — DONE. A full `rules/**` scan finds no remaining single-value `status: Success` selectors; the only two that ever existed (`oci_compute_terminate`, `oci_console_login`) already use `status: [Success, '200']`. The invariant is now enforced repo-wide by `scripts/test_query_audit.py:test_oci_success_status_selectors_include_native_parser_code` (broadened from `rules/cloud/oci` to the whole `rules/**` tree).
3. **Provision the Fusion Apps source** (or keep `hunting/oci_iam_fusion_activity_correlation.json` catalog-only) once the log source is available — see Catalog-Only Queries above.
4. **Schedule `daily_health_check.py`** as a recurring routine that posts the banner + diff against the previous run; surface regressions before deploy.
5. **Codex review-gate adoption** — now enabled for every stop, so include unit-test / smoke-test deltas in commit messages so the reviewer has full context.
6. **Keep `queries/dashboard_inventory.json` regenerated** with dashboard changes (already enforced by the deploy script's `--export-inventory` mode).
7. **Expand `DET-MISS-002`** with a generated log-source field dictionary for parser fields and display labels.
8. **Expand live verification beyond Caldera discovery** so credential-access, lateral-movement, collection, and exfiltration have deterministic demo data.
9. **Add ingestion/validation checks for `test_data/`** datasets — DONE. `scripts/validate_synthetic_logs.py` now also runs a coverage gate (`find_uncovered_datasets`) that fails if any present `test_data/*.jsonl` lacks a schema contract, and `config/synthetic_log_contracts.json` adds contracts for `cloud_guard_instance_security.jsonl` and the optional `octo_apm_workshop_application_logs.jsonl`, so every dataset the ingest manifest knows about (20/20) is schema-validated. Runs clean (0 errors) over the full generated dataset set; regression-fenced in `scripts/test_validate_synthetic_logs.py`.
10. **Expand source rule coverage only after** log source mappings and test datasets exist for the new telemetry surface.
