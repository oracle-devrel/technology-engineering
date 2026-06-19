# Requirements: OCI Log Analytics Detections

**Defined:** 2026-05-14 (v1.0); v2.0 added 2026-05-15; v3.0 added 2026-05-17
**Core Value:** Every committed detection, query, dashboard, parser mapping, and generated artifact must remain deployable and verifiable against OCI Log Analytics without leaking tenant-specific data.

## v1 Requirements

### GSD Project Operations

- [x] **GSD-01**: `.planning/PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md`, and `config.json` exist and describe the current brownfield project accurately.
- [x] **GSD-02**: `.planning/codebase/**` documents summarize stack, architecture, integrations, conventions, tests, structure, and concerns.
- [x] **GSD-03**: `AGENTS.md` tells Codex to use GSD workflows and this repo's artifact boundaries for future development.
- [x] **GSD-04**: Future substantial work can start from `$gsd-plan-phase <phase>` without re-discovering the repo from scratch.

### Detection Content Integrity

- [x] **DET-01**: Source Sigma/YAML rules include required metadata: stable ID, version, MITRE tags where applicable, and falsepositive guidance.
- [x] **DET-02**: Sigma-derived query artifacts are regenerated through `scripts/convert_sigma.py` and cataloged by `scripts/generate_catalog.py`.
- [x] **DET-03**: Rule quality audit reports zero critical, high, medium, and low findings before release.
- [x] **DET-04**: Atomic Red Team mapping coverage remains generated from the current catalog and reported in `docs/ART_COVERAGE_REPORT.md`.

### Sentinel Conversion

- [x] **SEN-01**: Sentinel mapping changes are made in `config/sentinel_oci_mapping.yaml` or converter code, not by hand-editing promoted JSON.
- [x] **SEN-02**: Promoted Sentinel queries have `source_type: microsoft_sentinel`, `conversion_status: promoted`, and `live_validation_status: passed`.
- [x] **SEN-03**: `queries/sentinel_conversion_report.json` records skipped candidates, local failures, live failures, and promoted counts.
- [x] **SEN-04**: Sentinel dashboard groups remain dry-run valid after conversion refreshes.

### Dashboard and Parser Contracts

- [x] **DASH-01**: Dashboard definitions in `scripts/deploy_dashboard.py` reference existing query files and pass dry-run validation.
- [x] **DASH-02**: Dashboard inventory is regenerated from code and reconciles to README/STATUS counts.
- [x] **DASH-03**: App/APM analytics remain on `SOC Application Logs` and pass `scripts/test_app_query_contract.py`.
- [x] **DASH-04**: Octo APM workshop bundle continues to include only the scoped dashboard/query/detection-rule assets required for downstream workshop deployment.
- [x] **DASH-05**: Parser and field-source dictionaries are regenerated after source, parser, or synthetic-log contract changes.

### Release and Verification

- [x] **REL-01**: Local release gates run through `scripts/release_checklist.py` or equivalent focused commands before a handoff.
- [x] **REL-02**: `python3 -m pytest -q` passes before changes are considered complete.
- [x] **REL-03**: `python3 scripts/deploy_dashboard.py --dry-run` passes after dashboard or query inventory changes.
- [x] **REL-04**: Optional live verification is explicit and profile-driven; no live mutation happens in local-only release gates.
- [x] **REL-05**: Generated docs and inventories are updated together when counts or artifacts change.

### Security and Data Hygiene

- [x] **SEC-01**: No committed file contains real credentials, API keys, private endpoints, OCIDs, public IPs, or tenant-specific values.
- [x] **SEC-02**: Error handling in scripts does not hide validation failures that should block release.
- [x] **SEC-03**: OCI operations require explicit profile/config inputs and remain dry-run or validation-only unless deployment is requested.

## v2.0 Requirements — Sentinel KQL Parity to Logan QL

Baseline (from `queries/sentinel_conversion_report.json`): 4,452 candidates, 25 attempted, 8 promoted, 10 live-failed, 17 skipped. Goal: close the conversion gap so promoted Sentinel content can grow toward thousands of queries with live OCI parser validation as the only promotion gate.

### Converter Refactor and Test Harness

- [ ] **REF-01**: `scripts/convert_sentinel_kql.py` is reduced to a thin facade (≤ 800 lines) over a new `scripts/kql/` subpackage containing `lexer.py`, `ast_nodes.py`, `pipeline.py`, `mapping_loader.py`, `operators/<op>.py`, `functions/<fn>.py`, and `emitter.py`, dispatched through an `OPERATOR_REGISTRY` mapping.
- [ ] **REF-02**: A Logan QL canonicalizer (`scripts/kql/canonical.py`) tokenizes converter output, sorts commutative comparisons, and normalizes quoting and whitespace so converter tests assert on canonical form rather than exact strings.
- [ ] **REF-03**: KQL expressions are classified as TIER-1 (lossless), TIER-2 (transform with documented rewrite), or TIER-3 (unsupported, SKIPPED with structured reason); the classifier output is included in `queries/sentinel_conversion_report.json`.
- [ ] **REF-04**: `requirements-dev.txt` introduces `pytest >= 8.3` and `hypothesis >= 6.150` (test-only — runtime deps in `requirements.txt` are unchanged); `scripts/test_kql/` mirrors the new subpackage tree with `fixtures/{kql,expected}/` directories.
- [ ] **REF-05**: Existing tests in `scripts/test_sentinel_converter.py` stay green throughout the refactor (behavior-preserving — REF-01..03 land without changing converter output for the current promoted set).

### Mapping Configuration and Field Coverage

- [x] **MAP-01**: `config/mapping/` shards the mapping schema by OCI data domain: `_root.yaml` + `tables/{identity,endpoint,cloud_azure,cloud_office,network}.yaml` + `fields/{common,subject,process,office,network}.yaml`; `config/sentinel_oci_mapping.yaml` is retained as a generated compatibility re-export.
- [x] **MAP-02**: `scripts/kql/mapping_loader.py` loads shards in deterministic order with a strict YAML loader that fails the build on duplicate keys; the first strict-load run is a documented, possibly-noisy task.
- [x] **MAP-03**: A collision lint pass detects many-to-one Sentinel-to-Logan column fan-outs (e.g., nine user-name fields mapping to `User Name`) and emits `lossy_mapping_collision:<a>+<b>→<col>` skip reasons; output written to `queries/mapping_collisions.json`.
- [x] **MAP-04**: Every mapped field carries a role tag from `{subject, target, initiator, resource, time, hash, network}` so role-mismatched comparisons (e.g., `subject == target`) can be detected by the converter.
- [ ] **MAP-05**: Bulk Sentinel field additions land for `SubjectAccount`, `SubjectDomainName`, `SubjectLogonId`, `SubjectUserSid`, `SubjectUserName`, `InitiatingProcessAccountDomain`, `InitiatingProcessAccountName`, `InitiatingProcessSHA256`, `InitiatingProcessId`, `MailboxOwnerUPN`, `OfficeWorkload`, `OrganizationName`, `ClientInfoString`, `UserType`, `ParentProcessName`, `ProcessId`, `Exe`, `LocalFile`, `ActingProcessFileInternalName`, plus a `Logon_Type` → `LogonType` alias.
- [ ] **MAP-06**: Every new mapping points to a key already present in `queries/log_source_field_dictionary.json` or carries a documented parser-source contract reference (see PARSER-01).

### KQL Operator Parity

- [ ] **OP-01**: `extend` with scalar functions (`iff`, `tostring`, `toint`, `tolong`, `tolower`, `toupper`) translates to OCL `eval` with the n-ary `if(...)` form.
- [ ] **OP-02**: Single-use `let` constant inlining is supported (multi-use and let-as-function remain SKIPPED with structured reason).
- [ ] **OP-03**: `bin(TimeGenerated, span)` translates to `timestats span=` against the matching time field; mixed-bin chains are SKIPPED.
- [ ] **OP-04**: `project`, `project-away`, `top N by`, `distinct`, `countif`, and `column_ifexists` (gated on MAP-05 completeness) translate to their OCL equivalents.
- [ ] **OP-05**: KQL `set timeout=...`, `set truncationmaxsize=...`, and `set query_take_max_records=...` directives are stripped silently rather than emitted as field-mapping failures.
- [ ] **OP-06**: Lossy emission is forbidden: `parse_command_line`, `parse with literal anchors`, true regex `matches regex`, `mv-expand`, `bag_unpack`, `series_*`, `geo_*`, cross-table `join`, `_GetWatchlist`, and `evaluate plugin(...)` remain SKIPPED with structured reasons; the converter must not silently rewrite them to weaker OCL equivalents.

### Parser-Side Field Extraction

- [ ] **PARSER-01**: Each Sentinel field that requires extraction beyond OCL field mapping (e.g., `EventData` children like `ObjectDN`, `ActingProcessFileInternalName`, certain `Office*` workload sub-fields) carries a documented parser readiness assessment under `docs/parser_readiness/<field>.md` capturing: source log type, current parser, gap, proposed extraction strategy, and SOC parser change scope.
- [ ] **PARSER-02**: At least the `EventData` ObjectDN/ObjectName/AttributeLDAPDisplayName trio is added to the relevant SOC parser (or a new parser definition under `config/parsers/`) and verified end-to-end against a synthetic fixture.
- [ ] **PARSER-03**: Fields whose extraction requires SOC parser changes outside this milestone's scope are marked `parser_change_required: true` in the mapping shards and SKIPPED with `parser_readiness:pending` reason until PARSER-02-style work lands.

### Backlog Prioritization

- [x] **PRI-01**: `scripts/sentinel_backlog_prioritize.py` emits `queries/sentinel_backlog_priority.json` ranking unmapped Sentinel candidates by MITRE coverage gap (joined against `queries/catalog.json`) × converter difficulty (joined against TIER classification from REF-03).
- [x] **PRI-02**: An "unblock chain length" metric annotates each skipped candidate with how many other candidates would promote if the same blocker were resolved; this guides cohort selection.
- [x] **PRI-03**: The prioritized backlog is wired as an advisory (non-blocking) line in `scripts/release_checklist.py` summary output.
- [x] **PRI-04**: `sync_sentinel_kql.py` candidate sync is rerun as an entry condition for any PRI-driven cohort selection so MITRE quality scoring reflects current Sentinel content.

### Drift and Synthetic-Hit Gates

- [ ] **DRIFT-01**: `scripts/sentinel_drift_check.py` diffs the current `queries/sentinel_conversion_report.json` against the `main:` baseline plus per-file `live_validation_status` and Logan QL body hashes; writes `queries/sentinel_drift.json` and exits non-zero on regression.
- [ ] **DRIFT-02**: Every promoted artifact in `queries/sentinel/*.json` records a `parser_schema_hash` derived deterministically from `queries/log_source_field_dictionary.json`; drift in this hash without an explicit promotion run flags as a drift incident.
- [ ] **DRIFT-03**: `scripts/release_checklist.py` adds a `live_synthetic_hit_count > 0` gate — every promoted Sentinel artifact must pair with a synthetic-log fixture producing at least one row.
- [ ] **DRIFT-04**: `queries/sentinel_conversion_report.json` separates `live_validation_passed_with_rows` from `live_validation_passed_zero_rows` in the summary so zero-row passes do not inflate promotion claims.

### CI and Live-Validation Lane

- [ ] **CI-01**: `.github/workflows/sentinel-converter.yml` runs four jobs on PRs that touch `scripts/`, `config/mapping/`, or `queries/`: `unit` (operator tests, no OCI), `integration` (dry-run full corpus, no live calls), `drift` (vs `main` baseline), and `live` (manual `workflow_dispatch` or scheduled cron, OCI secrets, delta-only).
- [ ] **CI-02**: The CI summary comment posts the backlog-priority delta and drift-detector results on every PR.
- [ ] **CI-03**: The Sentinel workflow's classifier treats `429 / RequestThrottled / TooManyRequests` as `live_environment` defect (retry-eligible) rather than `live_validation` failure (promotion-blocking).
- [ ] **CI-04**: Live calls in CI are cached on `(logan_ql_hash, parser_schema_hash, lookback)` with a configurable TTL so re-runs against unchanged candidates do not burn API budget.
- [ ] **CI-05**: `scripts/scan_sensitive_values.py` runs over `queries/sentinel/*.json` and `queries/sentinel_conversion_report.json` after promotion (not just before commit) with extended patterns covering OCIDs, public IPs, compartment names, and tenancy host suffixes.
- [ ] **CI-06**: `scripts/check_inventory_drift.py` is extended to cover Sentinel JSON ↔ conversion report ↔ catalog ↔ manifest reconciliation so drift in any of those four artifacts fails the PR.

## v3.0 Requirements - Logan QL Conversion Workbench

Baseline: this repo remains the canonical producer of OCI Log Analytics detection, conversion, reference, dashboard, and Forge webapp artifacts. The v3.0 frontend lives in `webapp/` and consumes generated artifacts from this repo.

### Workbench User Experience

- [ ] **WB-01**: The integrated `webapp/` frontend provides a source language selector and editor for Splunk SPL, Microsoft Sentinel KQL, Elastic/Lucene/KQL, Sigma/YAML, and OCI Log Analytics QL passthrough.
- [ ] **WB-02**: The workbench shows OCI Log Analytics QL output with formatting, copy, export, and warning states alongside a source-to-target explanation panel.
- [ ] **WB-03**: The workbench includes 10-20 validated example conversions across the supported source languages, with expected OCI QL and warning metadata.

### OCI Reference Catalog

- [ ] **REFCAT-01**: This repo generates `queries/logan_ql_reference_catalog.json` from official OCI Log Analytics documentation URLs, including command names, source URLs, retrieval timestamp, syntax summary, examples when available, and command category metadata.
- [ ] **REFCAT-02**: The integrated `webapp/` command/reference menu consumes the generated catalog rather than hand-authored React data, and includes query-search fundamentals plus command-reference entries.
- [ ] **REFCAT-03**: Catalog refresh tests fail when required command metadata is missing, provenance is absent, or generated menu data is edited manually.

### Cross-QL Conversion Patterns

- [ ] **XQL-01**: This repo generates a cross-QL pattern library covering filters, field references, boolean logic, time windows, aggregation, projection, eval/extend, regex/extraction, lookup/watchlist semantics, joins/correlation, sort/top, and unsupported constructs for Splunk SPL, Sentinel KQL, Elastic/Lucene/KQL, Sigma/YAML, and OCI QL.
- [ ] **XQL-02**: Conversion responses include structured explanations mapping source clauses to OCI Log Analytics commands, target fields, parser assumptions, support level, and warning messages.
- [ ] **XQL-03**: Lossy or unsupported source constructs produce explicit warnings or blocked conversions; the workbench must not silently emit weaker OCI QL.

### Producer/Consumer API Contract

- [ ] **API-01**: This repo defines versioned JSON schemas under `schemas/logan_workbench/` for workbench artifacts, conversion requests, conversion responses, examples, warnings, and reference catalog entries.
- [ ] **API-02**: The integrated `webapp/` frontend validates imported artifacts against the generated schemas at build time or startup and fails clearly when versions drift.
- [ ] **API-03**: Sentinel and Sigma examples reuse this repo's existing converter/mapping paths; `webapp/` does not duplicate converter generation logic.

### Documentation and Mapping Guidance

- [ ] **DOC-01**: `docs/logan_workbench_mapping_guide.md` explains how to map Splunk SPL, Sentinel KQL, Elastic/Lucene/KQL, Sigma/YAML, and generic source-query constructs to OCI Log Analytics QL with support-level notes.
- [ ] **DOC-02**: The integrated `/forge` page presents mapping guidance contextually through the command menu, examples, and explanation panel rather than as a standalone marketing page.

### Validation, Security, and Release Gates

- [ ] **QA-01**: Producer-side tests validate generated schemas, command catalog, mapping patterns, examples, and conversion warning behavior.
- [ ] **QA-02**: Workbench examples and synthetic logs contain no credentials, OCIDs, public IPs, tenancy-specific names, or unredacted live payloads; sensitive-value scanning covers the new artifacts.
- [ ] **QA-03**: `webapp/` gates include build, typecheck, lint, accessibility-sensitive browser checks, mobile/desktop layout checks, and the editor-to-output-to-copy/export flow.

## v2 Requirements (deferred — superseded or follow-on)

### Automation Improvements (carryover)

- **AUTO-01**: ~~CI workflow coverage for release-checklist dry-run gates.~~ → Superseded by CI-01.
- **AUTO-02**: Machine-readable GSD phase status export for companion project dashboards. → Carried forward.
- **AUTO-03**: ~~Automatic drift detection for README/STATUS counts against `queries/catalog.json`.~~ → Subsumed by CI-06.
- **AUTO-04**: ~~Prioritization helpers for Sentinel next-query backlog categories.~~ → Superseded by PRI-01..04.

### Coverage Expansion

- **COV-01**: Improve Sentinel live-pass coverage beyond the current 8 promoted queries. → Becomes the implicit success metric of v2.0; explicit target settings tracked in ROADMAP.md success criteria (Phase 9 target: 50–100 promoted).
- **COV-02**: Expand Atomic Red Team coverage for eligible non-OCI detections. → Carried forward.
- **COV-03**: Add more cloud-to-endpoint and app-to-cloud attack-path dashboards where parser contracts are validated. → Carried forward.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Additional companion UI implementation outside `webapp/` | Belongs in separate repos only if they consume generated artifacts and do not become the source of truth |
| Live OCI deployment by default | Requires explicit profile, compartment, and operator approval |
| Manual promoted Sentinel JSON patches | Breaks converter traceability and live-validation guarantees |
| New top-level workflow surfaces outside `skills/` | Existing project guidance prefers skills-first workflow surfaces |
| KQL ML operators (`series_*`, `autocluster`, `series_outliers`) | OCL has no ML primitive; route to OCI Anomaly Detection if needed |
| `geo_*` functions | No OCL geo plugin; push to parser-side enrichment |
| Dynamic-bag expansion (`parse_json`, `bag_unpack`, `todynamic`) | OCL field model is flat; extraction belongs in parsers |
| Cross-table `join kind=inner|leftouter` with `summarize` | Produce two saved searches + dashboard-level correlation instead |
| `_GetWatchlist()` watchlist hydration | Sentinel watchlists are external state; inlining IOCs into queries violates the no-PII rule |
| KQL stored-function inlining (`invoke FuncName(...)`) | Recursive, version-skewed; mechanical inlining is unsafe |
| Lossy `parse_command_line` emission | Corrupts detections silently; must remain SKIPPED |
| Lark / ANTLR-based KQL grammar | Over-engineered for current 6-shape unsupported set; revisit if count > 25 |
| `pythonnet` + `Kusto.Language` binding | Broken on macOS/Linux ARM + .NET 9 (pythonnet#2514) |
| Auto-created OCI scheduled-search alarms from Sentinel content | Detection rule specs remain metadata/export artifacts per v1.0 SEC-03 |
| OCI Lookups-backed watchlist replacement | Separate post-v2.0 epic |
| `union T1, T2` cross-source detections | Defer to v2.1+ unless cross-source demand becomes explicit |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| GSD-01 | Phase 1 | Complete |
| GSD-02 | Phase 1 | Complete |
| GSD-03 | Phase 1 | Complete |
| GSD-04 | Phase 1 | Complete |
| DET-01 | Phase 2 | Complete |
| DET-02 | Phase 2 | Complete |
| DET-03 | Phase 2 | Complete |
| DET-04 | Phase 2 | Complete |
| SEN-01 | Phase 3 | Complete |
| SEN-02 | Phase 3 | Complete |
| SEN-03 | Phase 3 | Complete |
| SEN-04 | Phase 3 | Complete |
| DASH-01 | Phase 4 | Complete |
| DASH-02 | Phase 4 | Complete |
| DASH-03 | Phase 4 | Complete |
| DASH-04 | Phase 4 | Complete |
| DASH-05 | Phase 4 | Complete |
| REL-01 | Phase 5 | Complete |
| REL-02 | Phase 5 | Complete |
| REL-03 | Phase 5 | Complete |
| REL-04 | Phase 5 | Complete |
| REL-05 | Phase 5 | Complete |
| SEC-01 | Phase 5 | Complete |
| SEC-02 | Phase 5 | Complete |
| SEC-03 | Phase 5 | Complete |
| REF-01 | Phase 6 | Pending |
| REF-02 | Phase 6 | Pending |
| REF-03 | Phase 6 | Pending |
| REF-04 | Phase 6 | Pending |
| REF-05 | Phase 6 | Pending |
| MAP-01 | Phase 7 | Pending |
| MAP-02 | Phase 7 | Pending |
| MAP-03 | Phase 7 | Pending |
| MAP-04 | Phase 7 | Pending |
| MAP-05 | Phase 9 | Pending |
| MAP-06 | Phase 9 | Pending |
| OP-01 | Phase 9 | Pending |
| OP-02 | Phase 9 | Pending |
| OP-03 | Phase 9 | Pending |
| OP-04 | Phase 9 | Pending |
| OP-05 | Phase 9 | Pending |
| OP-06 | Phase 9 | Pending |
| PARSER-01 | Phase 9 | Pending |
| PARSER-02 | Phase 9 | Pending |
| PARSER-03 | Phase 9 | Pending |
| PRI-01 | Phase 8 | Complete |
| PRI-02 | Phase 8 | Complete |
| PRI-03 | Phase 8 | Complete |
| PRI-04 | Phase 8 | Complete |
| DRIFT-01 | Phase 10 | Pending |
| DRIFT-02 | Phase 10 | Pending |
| DRIFT-03 | Phase 10 | Pending |
| DRIFT-04 | Phase 10 | Pending |
| CI-01 | Phase 11 | Pending |
| CI-02 | Phase 11 | Pending |
| CI-03 | Phase 11 | Pending |
| CI-04 | Phase 11 | Pending |
| CI-05 | Phase 11 | Pending |
| CI-06 | Phase 11 | Pending |
| WB-01 | Phase 15 | Pending |
| WB-02 | Phase 15 | Pending |
| WB-03 | Phase 16 | Pending |
| REFCAT-01 | Phase 13 | Pending |
| REFCAT-02 | Phase 13 | Pending |
| REFCAT-03 | Phase 13 | Pending |
| XQL-01 | Phase 14 | Pending |
| XQL-02 | Phase 14 | Pending |
| XQL-03 | Phase 14 | Pending |
| API-01 | Phase 12 | Pending |
| API-02 | Phase 12 | Pending |
| API-03 | Phase 12 | Pending |
| DOC-01 | Phase 14 | Pending |
| DOC-02 | Phase 15 | Pending |
| QA-01 | Phase 16 | Pending |
| QA-02 | Phase 16 | Pending |
| QA-03 | Phase 15 | Pending |

**Coverage:**
- v1 requirements: 25 total — all Complete (Phases 1–5)
- v2.0 requirements: 32 total — Pending (Phases 6–11)
- v3.0 requirements: 17 total — Pending (Phases 12–16)
- Mapped to phases: 49 (every v2.0 and v3.0 REQ-ID maps to exactly one phase)
- Unmapped: 0
- Orphaned phases: 0

---
*Requirements defined: 2026-05-14 (v1.0); v2.0 milestone added 2026-05-15*
*Last updated: 2026-05-17 - v3.0 Logan QL Conversion Workbench requirements and traceability added*
