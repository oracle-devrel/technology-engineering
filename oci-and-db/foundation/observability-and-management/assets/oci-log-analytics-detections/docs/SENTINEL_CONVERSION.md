# Microsoft Sentinel Conversion Workflow

Date: 2026-05-14

This document describes the Microsoft Sentinel KQL to OCI Log Analytics / Logan QL conversion path. It is intentionally conservative: local conversion is useful for development, but only live OCI parser-passing queries are promoted under `queries/sentinel/`.

## Current Baseline

- Official Microsoft Sentinel candidates available: 4,452
- Current canonical live report: 25 attempted, 8 promoted, 10 live failures
- Current promoted surface: 8 endpoint queries in `queries/sentinel/`, each live parser-passing and synthetic-row-backed
- Current Sentinel dashboard surface: 1 Endpoint Converted Detections dashboard with 8 widgets
- Previous full-promotion run failed uniformly with `query validation exceeded 20s`; use the synthetic parser loop for small batches before scaling again

The canonical machine-readable status is `queries/sentinel_conversion_report.json`. The static operator review page is `docs/sentinel_converter.html`.

## Surfaces

| Path | Purpose |
|------|---------|
| `.sentinel/Azure-Sentinel/` | Ignored local checkout of the official Microsoft Sentinel repository |
| `queries/sentinel_candidates.json` | Ignored/generated intake export from the Sentinel checkout |
| `config/sentinel_oci_mapping.yaml` | Allow-list of supported Sentinel tables and real OCI Log Analytics field mappings |
| `scripts/sync_sentinel_kql.py` | Fetch and normalize Analytics Rules and Hunting Queries YAML |
| `scripts/convert_sentinel_kql.py` | Deterministic converter and local/live validation engine |
| `scripts/sentinel_conversion_workflow.py` | Operator wrapper for local reports, promotion, artifact refresh, and HTML page generation |
| `scripts/sentinel_synthetic_logs.py` | Parser-aware synthetic-log planner/uploader/live checker for converted Sentinel batches |
| `queries/sentinel/*.json` | Promoted, live-validated saved-search query JSON |
| `queries/sentinel_conversion_report.json` | Conversion report with skip and live-failure reasons |
| `queries/sentinel_synthetic_plan.json` | Generated synthetic-log readiness and OCI parser/source gap report |
| `queries/sentinel_synthetic_live_results.json` | Generated live query result evidence for synthetic-ready candidates |
| `test_data/sentinel_synthetic/*.jsonl` | Generated Sentinel synthetic NDJSON grouped by parser-ready OCI source |
| `docs/sentinel_converter.html` | Static web review page built from the latest conversion report |

## Operator Commands

Use the wrapper for normal work:

```bash
# Fast local report. Does not overwrite the canonical live report.
python3 scripts/sentinel_conversion_workflow.py local

# Live-validate and write only working Sentinel queries.
python3 scripts/sentinel_conversion_workflow.py promote --top all --timeout 20

# Verbose live validation progress for long runs.
python3 scripts/sentinel_conversion_workflow.py promote --top all --timeout 60 --progress-interval 0

# Regenerate catalog, dashboard inventory, dashboard validation, and HTML page.
python3 scripts/sentinel_conversion_workflow.py refresh-artifacts

# Full promotion workflow.
python3 scripts/sentinel_conversion_workflow.py all --top all --timeout 20

# Rebuild the static HTML report only.
python3 scripts/sentinel_conversion_workflow.py page

# Summarize skip reasons, local validation errors, live failures, and next actions.
python3 scripts/sentinel_conversion_workflow.py triage
python3 scripts/sentinel_conversion_workflow.py triage --json

# List concrete candidates to develop next.
python3 scripts/sentinel_conversion_workflow.py next-queries --limit 10
python3 scripts/sentinel_conversion_workflow.py next-queries --strategy foundational --limit 10
python3 scripts/sentinel_conversion_workflow.py next-queries --work-type field_mapping --json

# Generate parser-aware synthetic logs and explicit OCI parser/source gaps for a small batch.
python3 scripts/sentinel_conversion_workflow.py synthetic-plan --top 25 --progress-interval 0

# Check report, promoted files, and Sentinel dashboard consistency.
python3 scripts/sentinel_conversion_workflow.py status
python3 scripts/sentinel_conversion_workflow.py status --json
python3 scripts/sentinel_conversion_workflow.py status --json --strict
```

The low-level converter remains available when a focused debugging run is needed:

```bash
python3 scripts/convert_sentinel_kql.py --top 4452 --validate-local --no-sync --report /tmp/sentinel_conversion_local.json
python3 scripts/convert_sentinel_kql.py --top 4452 --validate-live --write-working --clean-output --no-sync --query-timeout 20
python3 scripts/convert_sentinel_kql.py --top 5 --validate-live --write-working --output-dir /tmp/sentinel_live_smoke --report /tmp/sentinel_live_smoke.json --no-sync --query-timeout 60 --progress-interval 0
```

## Progress Output

The converter emits periodic progress lines to stderr. Live validation runs always print `live-start`, `live-passed` or `live-failed`, candidate index, quality score, title, source path, query file, and validation duration. Local runs print start, periodic candidate status, counters, and final summary.

Progress controls:

- `--progress-interval 30`: default periodic progress cadence in seconds
- `--progress-interval 0`: print every candidate, useful for long live validation debugging
- `--progress-interval -1`: disable progress lines
- `--progress-every 100`: emit at least one candidate status line every N attempted candidates

Progress output intentionally avoids query text, OCIDs, request IDs, profile names, and credentials.

## Synthetic Parser Loop

`scripts/sentinel_synthetic_logs.py` is the batch loop for building the data and parser side of Sentinel promotion. It is intentionally staged so a live CAP run can be performed in small groups instead of attempting all candidates blindly.

Planner mode converts the requested top batch, derives the Logan fields used by each converted query, checks those fields against existing parser/source contracts from `scripts/setup_log_sources.py`, and writes NDJSON only when every required field is backed by an existing parser mapping:

```bash
python3 scripts/sentinel_synthetic_logs.py plan --top 25 --progress-interval 0
```

The generated report records `synthetic_ready`, `source_gap`, `field_gap`, and `conversion_skipped` candidates. Gaps include the ordered OCI work needed before promotion: confirm source, define parser, define fields/aliases, ingest representative logs, validate in CAP, update the field dictionary, add the allow-list mapping, and add converter tests.

Upload and live-check modes are separate so operators can inspect the plan before writing to CAP:

```bash
python3 scripts/sentinel_synthetic_logs.py upload --dry-run
python3 scripts/sentinel_synthetic_logs.py upload
python3 scripts/sentinel_synthetic_logs.py validate-live --limit 8 --timeout 60 --lookback 24h
python3 scripts/sentinel_synthetic_logs.py promote-validated --clean-output
```

After synthetic logs are processed by OCI Log Analytics, live validation should be run per small group. Only queries that pass live validation and return the expected synthetic evidence should be promoted with `sentinel_synthetic_logs.py promote-validated`; do not copy planner output into `queries/sentinel/`.

## Promotion Rules

- Source content must come from the official `Azure/Azure-Sentinel` repository.
- `config/sentinel_oci_mapping.yaml` is an allow-list, not a guess table.
- Mapped Logan fields must exist in `queries/log_source_field_dictionary.json`, approved converter built-ins, or the approved Azure audit schema fields.
- `queries/sentinel/*.json` must only contain queries with `conversion_status: promoted` and `live_validation_status: passed`.
- Nonworking candidates stay in `queries/sentinel_conversion_report.json`; they are not written as saved-search files.
- No alarms or Terraform apply are part of this workflow.

## Converter Guardrails

The converter strips explicit KQL time filters such as `TimeGenerated > ago(...)`; OCI validation and dashboard time windows provide the runtime range.

KQL `filter <predicate>` is supported as an alias for `where <predicate>`, so predicates flow through the same deterministic field mapping and operator conversion path.

Summarize aggregate aliases are kept unique. When generated aliases collide, the converter appends deterministic numeric suffixes such as `any_Time_2` instead of emitting duplicate Logan aliases.

Local validation rejects `| stats ... by Time` with `unsupported OCI time grouping: Time`. Time-bucket support remains blocked until a deterministic OCI-compatible implementation is added and live-validated.

The converter drops Microsoft Sentinel entity-binding aliases such as:

- `AccountCustomEntity`
- `HostCustomEntity`
- `IPCustomEntity`
- `URLCustomEntity`
- `DNSCustomEntity`
- `MalwareCustomEntity`

The converter rejects unresolved placeholders and unsupported KQL-only constructs, including:

- `{{...}}`, `GOES HERE`, `REPLACE_ME`, `CHANGE_ME`, `YOUR_VALUE`
- colon parameters such as `:user` or `:attack_id`
- tabular `let`, `join`, `make-series`, `mv-expand`, `datatable`, watchlists, `externaldata`, custom functions
- regex extraction/predicate and complex JSON bag expansion
- unsupported function leakage such as `strlen`, `toint`, or raw `int(...)`

High-volume KQL feature families such as `join`, `mv-expand` / `mv-apply`, JSON bag expansion, and arbitrary regex extraction/predicates remain intentionally unsupported. Do not convert them partially or lossily; add deterministic Logan semantics and tests first.

## Generated Dashboards

`scripts/deploy_dashboard.py` builds five Sentinel dashboard groups from live-passing query JSON only:

- `SOC: Microsoft Sentinel Identity Converted Detections`
- `SOC: Microsoft Sentinel Endpoint Converted Detections`
- `SOC: Microsoft Sentinel Azure Cloud Converted Detections`
- `SOC: Microsoft Sentinel M365 Converted Detections`
- `SOC: Microsoft Sentinel Network Converted Detections`

Each group is capped at 24 widgets. If a category has fewer live-passing queries, the dashboard contains only the available live-passing widgets.

## Web Review Page

`docs/sentinel_converter.html` is static and can be opened directly in a browser. It shows:

- candidate and promotion counts
- live pass/fail totals
- promoted query category mix
- Sentinel dashboard widget counts
- top skip reasons
- redacted live-validation failure summaries

The page intentionally redacts OCI request identifiers from live validation errors.

## Triage

`python3 scripts/sentinel_conversion_workflow.py triage` is a no-write report reader for converter follow-up work. It summarizes:

- top skip reasons from attempted candidates
- top local validation errors
- top unsupported feature counters
- redacted live-validation failure examples
- next actions for field mapping, table mapping, local validation, and live-parser fixes

Use `--json` when `webapp/`, a downstream UI, or a backlog-generation job needs structured triage output. Use `--limit` to control how many rows are returned per section.

## Developing The Next Queries

Use `python3 scripts/sentinel_conversion_workflow.py next-queries` to pick the next specific Sentinel candidates to work on. The command reads the existing report and returns a quality-aware backlog with these work types:

- `live_environment`: live validation failed because of auth, tenancy, or clock-skew conditions; rerun validation before changing converter logic
- `live_validation`: closest to promotion; generated Logan QL exists but the OCI parser rejected it
- `local_validation`: converter output exists but local guardrails failed
- `field_mapping`: a Sentinel field needs a real OCI field mapping
- `table_mapping`: a Sentinel table needs a real OCI source/parser mapping
- `kql_support`: deterministic converter support may be needed for a KQL feature
- `unsupported`: keep skipped unless a real mapping or deterministic implementation is added

The default strategy is live-first and preserves the existing order: `live_environment`, `live_validation`, `local_validation`, `field_mapping`, `table_mapping`, `kql_support`, then `unsupported`. Use it when the goal is to move candidates closest to promotion through local/live validation.

The foundational strategy is support-first and uses this order: `field_mapping`, `table_mapping`, `kql_support`, `local_validation`, `live_validation`, `live_environment`, then `unsupported`. Use `python3 scripts/sentinel_conversion_workflow.py next-queries --strategy foundational --limit 10` when the goal is to invest in field, table, and KQL support that unlocks larger future batches.

For `field_mapping` and `table_mapping` candidates, JSON output includes an additive `oci_gap` object with:

- `gap_type`: `field_mapping` or `table_mapping`
- `blocked_on`: the missing Sentinel field or table parsed from the skip reason
- `oci_steps`: ordered OCI follow-up labels

The OCI parser/source checklist is:

1. confirm OCI source
2. define parser or parser mapping
3. define fields and aliases
4. ingest representative sample logs
5. validate in CAP tenancy
6. update field dictionary
7. add allow-list mapping
8. add converter tests

These steps implement the Phase 3 parser/source policy: create or enable the Log Analytics source, define parser behavior and field aliases, ingest representative logs, validate in CAP without committing tenancy-specific details, update `queries/log_source_field_dictionary.json`, update sample or synthetic contracts when needed, then add the mapping and focused converter tests.

Current Phase 3 mapping examples:

- `ThreatActionTaken` from `McAfeeEPOEvent` maps to dictionary-backed `Action`.
- `TheomAlerts_CL` remains unsupported because there is no documented OCI source/parser contract for that vendor custom table. Required follow-up is to confirm an OCI Theom source, define parser mappings for fields such as `customProps_RuleId_s` and `priority_s`, ingest representative Theom alert samples, validate in CAP, update the field dictionary, then add table mapping and converter tests.

Recommended loop for later/new Sentinel query development:

1. Run `python3 scripts/sentinel_conversion_workflow.py triage --limit 10`.
2. Pick a small queue with `python3 scripts/sentinel_conversion_workflow.py next-queries --strategy foundational --work-type <type> --limit 10` for support-first work, or omit `--strategy foundational` for live-first work.
3. For `field_mapping` or `table_mapping`, verify the target against `queries/log_source_field_dictionary.json` or approved converter built-ins before editing `config/sentinel_oci_mapping.yaml`.
4. For `kql_support` or `local_validation`, add deterministic converter behavior and focused tests in `scripts/test_sentinel_converter.py`.
5. Run `python3 scripts/sentinel_conversion_workflow.py local`; do not write files under `queries/sentinel/` by hand.
6. Promote only with live validation: `python3 scripts/sentinel_conversion_workflow.py promote --top all --timeout 20`.
7. Run `refresh-artifacts`, `page`, `status --json --strict`, focused tests, and the full verification loop.

`next-queries --json` is intended for `webapp/`, downstream UIs, or backlog automation. It includes the candidate title, Sentinel ID, quality score, source path/URL, work type, reason, and next step.

## Status Check

`python3 scripts/sentinel_conversion_workflow.py status` is the fastest no-write health check for the Sentinel surface. It compares:

- `summary.promoted_count` in `queries/sentinel_conversion_report.json`
- the number of promoted JSON files in `queries/sentinel/`
- `summary.live_validation_passed`
- live-validation status values inside promoted query JSON
- Sentinel dashboard presence in `queries/dashboard_inventory.json`

Use `--json` when `webapp/`, a downstream UI, MCP server, or CI job needs a machine-readable summary. Add `--strict` when the command should exit non-zero if the report, promoted files, live status, or Sentinel dashboard inventory needs attention. For isolated checks, override the artifact locations with `--report`, `--sentinel-dir`, and `--dashboard-inventory`.

## Validation

After Sentinel converter, mapping, query, or documentation changes, run:

```bash
python3 -m pytest scripts/test_sentinel_converter.py scripts/test_sentinel_conversion_workflow.py -q
python3 scripts/sentinel_conversion_workflow.py page
python3 scripts/generate_catalog.py
python3 scripts/deploy_dashboard.py --export-inventory
python3 scripts/deploy_dashboard.py --validate
python3 -m compileall scripts
```

For a full confidence pass, run `python3 -m pytest -q`.
