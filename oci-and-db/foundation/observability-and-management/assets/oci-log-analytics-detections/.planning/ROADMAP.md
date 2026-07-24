# Roadmap: OCI Log Analytics Detections

## Overview

This roadmap turns the existing OCI Log Analytics detection repository into a GSD-managed brownfield project. Phases 1-5 (milestone v1.0) established durable project state and hardened detection content, Sentinel conversion, dashboards, parser contracts, and release evidence. Phases 6-11 (milestone v2.0 "Sentinel KQL Parity to Logan QL") close the conversion gap between Microsoft Sentinel KQL and OCI Log Analytics QL so the converter can move promoted Sentinel content from the original 8 promoted-query baseline toward thousands, with live OCI parser validation remaining the sole promotion gate. Phases 12-16 (milestone v3.0 "Logan QL Conversion Workbench") add the integrated `webapp/` frontend while this repo remains the producer of conversion, reference, example, and schema artifacts.

## Phases

- [x] **Phase 1: GSD Brownfield Baseline** - Add planning state, codebase map, and Codex-facing GSD guidance.
- [x] **Phase 2: Detection Integrity Gates** - Tighten source-rule, query-generation, catalog, ART, and rule-quality loops.
- [x] **Phase 3: Sentinel Conversion Backlog** - Systematically reduce Sentinel skipped/local-failure/live-failure backlog.
- [x] **Phase 4: Dashboard and Parser Contract Hardening** - Keep dashboards, field dictionaries, synthetic logs, and Octo workshop assets aligned.
- [x] **Phase 5: Release and Security Automation** - Make local/live verification and secret hygiene repeatable before handoff.
- [x] **Phase 6: KQL Subpackage Extraction and Canonicalizer** - Behavior-preserving refactor of the Sentinel converter and golden-fixture test harness.
- [x] **Phase 7: Mapping Config Sharding and Collision Lint** - Shard `sentinel_oci_mapping.yaml`, add strict loader, role tags, and collision lint.
- [x] **Phase 8: Backlog Prioritizer and Cohort Overlay** - Rank unmapped Sentinel candidates by MITRE coverage × converter difficulty so Phases 9–10 work against cohorts, not throwaways.
- [ ] **Phase 9: Operator Parity and Field Mapping Bulk Expansion** - Land `extend`/`let`/`bin`/`project` family operators, parser-side extraction, and bulk Sentinel field additions in parallel cohort work.
- [ ] **Phase 10: Drift Detector and Synthetic-Hit Promotion Gate** - Prevent silent regressions and zero-row false passes once promotion scales.
- [ ] **Phase 11: CI Workflow with PR Dry-Run vs Scheduled-Live Lane Split** - Wire converter + drift + scan + inventory checks into CI; isolate live OCI calls to manual/scheduled jobs.
- [ ] **Phase 12: Frontend Boundary and Artifact/API Contract** - Define the integrated `webapp/` target, generated artifact set, schemas, and conversion request/response contract.
- [ ] **Phase 13: Official OCI Logan QL Reference Catalog** - Generate the workbench command menu from official OCI Log Analytics documentation with provenance and tests.
- [ ] **Phase 14: Cross-QL Conversion Pattern Library** - Build deterministic mapping patterns and explanations from Splunk, Sentinel, Elastic/Lucene/KQL, Sigma, and OCI passthrough into OCI Log Analytics QL.
- [ ] **Phase 15: Integrated Workbench UX** - Implement the real converter workbench surface in `webapp/` using generated artifacts.
- [ ] **Phase 16: Examples, Validation, and Release Gates** - Validate 10-20 conversions, scan workbench artifacts, and wire producer plus `webapp/` gates.

## Phase Details

### Phase 1: GSD Brownfield Baseline

**Goal**: The repo has a usable GSD project state and future agents can continue development from `.planning/**`.
**Depends on**: Nothing.
**Requirements**: GSD-01, GSD-02, GSD-03, GSD-04
**Success Criteria** (what must be TRUE):
  1. `.planning/PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md`, and `config.json` exist.
  2. `.planning/codebase/**` documents describe the current stack, architecture, integrations, conventions, testing, structure, and concerns.
  3. `AGENTS.md` tells Codex to use GSD and this repo's artifact boundaries.
  4. Full local tests pass after initialization.
**Plans**: 3 plans

Plans:
- [x] 01-01: Initialize GSD project docs from README, PLAN, STATUS, CLAUDE, and generated inventories.
- [x] 01-02: Add codebase map documents for architecture, stack, integrations, conventions, testing, structure, and concerns.
- [x] 01-03: Add Codex/GSD operating instructions and verify local tests.

### Phase 2: Detection Integrity Gates

**Goal**: Detection source changes regenerate and validate all dependent query/catalog artifacts reliably.
**Depends on**: Phase 1
**Requirements**: DET-01, DET-02, DET-03, DET-04
**Success Criteria** (what must be TRUE):
  1. Rule-quality audit remains zero issue after source changes.
  2. Source-derived queries and catalog outputs are regenerated through scripts, not manual edits.
  3. ART coverage report regenerates from the current catalog.
  4. README/STATUS count changes reconcile to `queries/catalog.json`.
**Plans**: 3 plans

Plans:
- [x] 02-01: Document and test the source-rule regeneration path.
- [x] 02-02: Add or tighten count-drift checks for catalog-facing docs.
- [x] 02-03: Improve ART coverage reporting and regression tests for eligible query surfaces.

### Phase 3: Sentinel Conversion Backlog

**Goal**: Sentinel conversion work is prioritized and reduces live/local failures without breaking promotion rules.
**Depends on**: Phase 2
**Requirements**: SEN-01, SEN-02, SEN-03, SEN-04
**Success Criteria** (what must be TRUE):
  1. Next-query backlog is reproducible from `queries/sentinel_conversion_report.json`.
  2. Promoted files remain live-validation-passed only.
  3. Converter tests cover any new KQL/function/table/field mapping behavior.
  4. Sentinel dashboard dry-runs stay valid.
**Plans**: 3 plans

Plans:
- [x] 03-01: Triage current Sentinel skip and failure buckets into actionable work queues.
- [x] 03-02: Add field/table mapping fixes with converter tests.
- [x] 03-03: Refresh promoted artifacts and dashboard groups after live validation.

### Phase 4: Dashboard and Parser Contract Hardening

**Goal**: Dashboards, parser mappings, synthetic logs, and workshop bundles remain consistent and deployable.
**Depends on**: Phase 3
**Requirements**: DASH-01, DASH-02, DASH-03, DASH-04, DASH-05
**Success Criteria** (what must be TRUE):
  1. Dashboard dry-run and inventory export pass after dashboard edits.
  2. Field dictionary reflects parser mappings, synthetic contracts, and query usage.
  3. App/APM queries pass the SOC Application Logs contract tests.
  4. Octo APM workshop bundle can be regenerated and consumed by downstream deployment scripts.
**Plans**: 4 plans

Plans:
- [x] 04-01: Strengthen dashboard inventory and query-file validation.
- [x] 04-02: Refresh field dictionary and synthetic-log contract checks.
- [x] 04-03: Guard app/APM and WAF cross-correlation query patterns.
- [x] 04-04: Verify Octo APM workshop bundle generation and downstream contract.

### Phase 5: Release and Security Automation

**Goal**: Handoffs are backed by repeatable local evidence, optional live verification, and secret hygiene.
**Depends on**: Phase 4
**Requirements**: REL-01, REL-02, REL-03, REL-04, REL-05, SEC-01, SEC-02, SEC-03
**Success Criteria** (what must be TRUE):
  1. `scripts/release_checklist.py` covers the expected local gates for non-live releases.
  2. Optional live verification requires explicit profile-driven invocation.
  3. Secret/tenant-specific value checks protect committed files.
  4. Release evidence is written under `docs/health/` when gates run.
**Plans**: 3 plans

Plans:
- [x] 05-01: Align release checklist with current generated artifact contract.
- [x] 05-02: Add secret and tenant-specific value scanning to the release path.
- [x] 05-03: Add handoff summary generation from release evidence and GSD state.

---

## Milestone v2.0 — Sentinel KQL Parity to Logan QL

Phases 6–11 deliver KQL operator parity, mapping completeness, drift protection, and CI lane separation. Phase numbering continues from v1.0. Baseline counters from `queries/sentinel_conversion_report.json`: 4,452 candidates, 25 attempted, **8 promoted**, 10 live-failed, 17 skipped. Target promoted_count by end of Phase 10: **50–100 queries** (conservative; research notes 7/10 current live failures close after Phase 9 mapping work).

- [x] **Phase 6:** KQL Subpackage Extraction and Canonicalizer
- [x] **Phase 7:** Mapping Config Sharding and Collision Lint
- [x] **Phase 8:** Backlog Prioritizer and Cohort Overlay
- [ ] **Phase 9:** Operator Parity and Field Mapping Bulk Expansion
- [ ] **Phase 10:** Drift Detector and Synthetic-Hit Promotion Gate
- [ ] **Phase 11:** CI Workflow with PR Dry-Run vs Scheduled-Live Lane Split

### Phase 6: KQL Subpackage Extraction and Canonicalizer

**Goal**: The Sentinel converter can be extended safely — file size is back under the 800-line ceiling, dispatch is registry-based, and converter tests assert on canonical Logan QL rather than brittle string equality.
**Depends on**: Phase 5
**Requirements**: REF-01, REF-02, REF-03, REF-04, REF-05
**Success Criteria** (what must be TRUE):
  1. `scripts/convert_sentinel_kql.py` is ≤ 800 lines and dispatches to `scripts/kql/` via an `OPERATOR_REGISTRY` mapping.
  2. `scripts/kql/canonical.py` roundtrips each currently-promoted Sentinel query (input → canonical form → input.canonical) without semantic loss.
  3. Existing `scripts/test_sentinel_converter.py` and the full `python3 -m pytest -q` suite stay green throughout the refactor (behavior-preserving).
  4. Every KQL expression in the corpus is classified as TIER-1 / TIER-2 / TIER-3 and the classifier output appears in `queries/sentinel_conversion_report.json`.
  5. `requirements-dev.txt` introduces `pytest >= 8.3` and `hypothesis >= 6.150` only; `requirements.txt` runtime deps (`oci`, `PyYAML`, `python-dotenv`) are unchanged.
**Exit Conditions**:
  - Promoted artifact set unchanged (8 queries, identical bodies after canonical normalization).
  - `scripts/test_kql/` mirror tree exists with `fixtures/{kql,expected}/` populated for at least every currently promoted query.
  - Release checklist (`python3 scripts/release_checklist.py`) still passes locally.
**Plans**: 10 plans

### Phase 7: Mapping Config Sharding and Collision Lint

**Goal**: The Sentinel→Logan mapping is shardable, role-aware, duplicate-detecting, and surfaces lossy many-to-one fan-out before it corrupts detections.
**Depends on**: Phase 6
**Requirements**: MAP-01, MAP-02, MAP-03, MAP-04
**Success Criteria** (what must be TRUE):
  1. `config/mapping/_root.yaml` plus `tables/{identity,endpoint,cloud_azure,cloud_office,network}.yaml` and `fields/{common,subject,process,office,network}.yaml` exist; `config/sentinel_oci_mapping.yaml` is retained as a generated compatibility re-export.
  2. `scripts/kql/mapping_loader.py` strict YAML loader fails the build with a non-zero exit and a `duplicate_key:<path>` reason when an injected duplicate key is added to any shard.
  3. The collision lint pass emits `lossy_mapping_collision:<a>+<b>→<col>` skip reasons for at least the known many-to-one cases (nine user-name fields fanned to `User Name`; `Computer`+`DeviceId` fanned to `Entity`) and writes them to `queries/mapping_collisions.json`.
  4. Every mapped field carries a role tag drawn from `{subject, target, initiator, resource, time, hash, network}`; a converter test asserts role-mismatched comparisons (`subject == target`) are detected and SKIPPED with `role_mismatch:<a>:<b>` reason.
**Exit Conditions**:
  - First strict-load run is documented in `docs/sentinel_mapping_strict_loader.md` with the duplicate-override findings it surfaces.
  - Promoted artifact set still re-validates against the sharded mapping (no regressions in promoted_count).
**Plans**: 4 plans

Plans:
- [x] 07-01: Shard schema and strict loader.
- [x] 07-02: Field role tags and role mismatch.
- [x] 07-03: Collision lint and generated report.
- [x] 07-04: Docs, status, and release gates.

### Phase 8: Backlog Prioritizer and Cohort Overlay

**Goal**: Phase 9 and Phase 10 work targets ranked cohorts instead of arbitrary candidates, so operator and mapping additions land where they unblock the most MITRE-relevant queries.
**Depends on**: Phase 7
**Requirements**: PRI-01, PRI-02, PRI-03, PRI-04
**Success Criteria** (what must be TRUE):
  1. `scripts/sentinel_backlog_prioritize.py` writes a non-empty, deterministically ordered `queries/sentinel_backlog_priority.json` ranking unmapped Sentinel candidates by MITRE coverage gap × converter TIER difficulty.
  2. Each ranked entry carries an `unblock_chain_length` metric counting how many other candidates would promote if the same blocker (operator, mapping, parser readiness) were resolved.
  3. `scripts/release_checklist.py` summary output includes an advisory (non-blocking) line of the form `Sentinel backlog: <N> ranked; top blocker: <reason>` driven by the prioritizer.
  4. `scripts/sync_sentinel_kql.py` is rerun as an explicit entry condition before each prioritizer run and the freshness timestamp is recorded inside the priority JSON.
**Exit Conditions**:
  - At least the top 20 backlog entries cite a concrete blocker reason traceable to either an operator in Phase 9 scope or a mapping field listed in MAP-05.
  - Prioritizer can be re-run idempotently and produces stable ordering for unchanged inputs.
**Plans**: 3 plans

Plans:
- [x] 08-01: Prioritizer generator.
- [x] 08-02: Release advisory and artifact contract.
- [x] 08-03: Docs, status, and gates.

### Phase 9: Operator Parity and Field Mapping Bulk Expansion

**Goal**: Promoted Sentinel coverage climbs from 8 toward a 50–100-query target by closing the dominant operator and mapping blockers in cohort-driven PRs, with parser-side extraction handled explicitly where OCL field mapping alone is insufficient.
**Depends on**: Phase 8
**Requirements**: MAP-05, MAP-06, OP-01, OP-02, OP-03, OP-04, OP-05, OP-06, PARSER-01, PARSER-02, PARSER-03
**Success Criteria** (what must be TRUE):
  1. `promoted_count` in `queries/sentinel_conversion_report.json` reaches at least **50** (target 100) with every promoted artifact still gated on live OCI parser validation — the live-validation promotion gate is **not** relaxed.
  2. `extend` with `iff`, `tostring`, `toint`, `tolong`, `tolower`, `toupper`; single-use `let` constant inlining; `bin(TimeGenerated, span) → timestats span=`; and `project` / `project-away` / `top N by` / `distinct` / `countif` / `column_ifexists` all translate to valid OCL with operator-level tests covering at least one promoted fixture each.
  3. Lossy emissions stay SKIPPED with structured reasons: `parse_command_line`, `parse with literal anchors`, true regex `matches regex`, `mv-expand`, `bag_unpack`, `series_*`, `geo_*`, cross-table `join`, `_GetWatchlist`, `evaluate plugin(...)` — a converter test injects each shape and asserts it does not silently rewrite to a weaker OCL form.
  4. KQL `set timeout=...`, `set truncationmaxsize=...`, and `set query_take_max_records=...` directives are stripped silently and no longer surface as `field_mapping_failure` in the report.
  5. The MAP-05 field cluster (`Subject*`, `InitiatingProcess*` extras, `MailboxOwnerUPN`, `OfficeWorkload`, `OrganizationName`, `ClientInfoString`, `UserType`, `ParentProcessName`, `ProcessId`, `Exe`, `LocalFile`, `ActingProcessFileInternalName`, `Logon_Type` alias) is fully mapped; every entry either resolves to a key already present in `queries/log_source_field_dictionary.json` or carries a documented parser-source contract reference under `docs/parser_readiness/<field>.md`.
  6. At least the `EventData` ObjectDN / ObjectName / AttributeLDAPDisplayName trio is wired through a SOC parser change verified end-to-end against a synthetic fixture; fields whose extraction requires SOC parser work outside this milestone are flagged `parser_change_required: true` in the mapping shards and SKIPPED with `parser_readiness:pending`.
**Exit Conditions**:
  - Each new operator translator and field mapping ships as its own PR with golden-fixture tests under `scripts/test_kql/`.
  - No hand-authored content lands under `logandetectionqueries/` or `logandetectionrules/`; new mappings reach promoted JSON only via the converter.
  - `python3 -m pytest -q` and `python3 scripts/deploy_dashboard.py --dry-run` still pass.
**Plans**: TBD

### Phase 10: Drift Detector and Synthetic-Hit Promotion Gate

**Goal**: Scaled promotion never silently regresses, and "compiles and runs" can no longer masquerade as "returns meaningful data" — both gates exist before promoted_count moves into the human-review-impractical range.
**Depends on**: Phase 9
**Requirements**: DRIFT-01, DRIFT-02, DRIFT-03, DRIFT-04
**Success Criteria** (what must be TRUE):
  1. `scripts/sentinel_drift_check.py` diffs current `queries/sentinel_conversion_report.json` against the `main:` baseline plus per-file `live_validation_status` and Logan QL body hashes, writes `queries/sentinel_drift.json`, and exits non-zero on regression — a test injects a mapping change that demotes a promoted file and confirms the checker fails.
  2. Every promoted artifact in `queries/sentinel/*.json` records a `parser_schema_hash` derived deterministically from `queries/log_source_field_dictionary.json`; drift in this hash without an explicit promotion run is flagged in `queries/sentinel_drift.json`.
  3. `scripts/release_checklist.py` enforces `live_synthetic_hit_count > 0` per promoted Sentinel artifact and blocks promotion (non-zero exit) when a promoted query produces zero rows against its paired synthetic-log fixture.
  4. `queries/sentinel_conversion_report.json` summary separates `live_validation_passed_with_rows` from `live_validation_passed_zero_rows`; the two counters reconcile to the existing `promoted_count`.
**Exit Conditions**:
  - Synthetic-fixture audit (Phase 10 plan) catalogs which promoted artifacts are missing a paired fixture and remediates or downgrades them before the gate is enforced.
  - Drift checker is wired into `scripts/release_checklist.py` and the local non-live gate path.
**Plans**: TBD

### Phase 11: CI Workflow with PR Dry-Run vs Scheduled-Live Lane Split

**Goal**: Pull requests get fast, deterministic verification while live OCI calls are isolated to manual/scheduled jobs with cached results, sensitive-value scanning, and full Sentinel↔report↔catalog↔manifest reconciliation.
**Depends on**: Phase 10
**Requirements**: CI-01, CI-02, CI-03, CI-04, CI-05, CI-06
**Success Criteria** (what must be TRUE):
  1. `.github/workflows/sentinel-converter.yml` runs four jobs on PRs that touch `scripts/`, `config/mapping/`, or `queries/`: `unit` (operator tests, no OCI), `integration` (dry-run full corpus, no live calls), `drift` (vs `main` baseline), `live` (`workflow_dispatch` or `schedule`, OCI secrets, delta-only) — fork PRs cannot reach org secrets and `live` is never auto-triggered on PR open.
  2. The Sentinel workflow's classifier treats `429`, `RequestThrottled`, and `TooManyRequests` as `live_environment` defects (retry-eligible) rather than `live_validation` failures, so throttling no longer blocks promotion in the report; a synthetic 429 fixture is asserted to be retry-eligible.
  3. Live calls in CI are cached on `(logan_ql_hash, parser_schema_hash, lookback)` with a configurable TTL; a re-run of the `live` job against an unchanged candidate set hits the cache and makes zero new OCI API calls.
  4. `scripts/scan_sensitive_values.py` runs over `queries/sentinel/*.json` and `queries/sentinel_conversion_report.json` after promotion (not only at pre-commit) with extended patterns covering OCIDs, public IPs, compartment names, and tenancy host suffixes; a seeded test secret in a fixture causes the scan to fail.
  5. `scripts/check_inventory_drift.py` is extended to reconcile Sentinel JSON ↔ `sentinel_conversion_report.json` ↔ `queries/catalog.json` ↔ `queries/manifest.json` and fails the PR when any of the four is out of sync.
  6. The CI summary comment posts backlog-priority delta and drift-detector results on every PR (delta vs `main:queries/sentinel_backlog_priority.json` and `main:queries/sentinel_drift.json`).
**Exit Conditions**:
  - The first scheduled `live` job runs against a representative delta, populates the cache, and posts results without blowing the OCI API budget.
  - `scripts/release_checklist.py --include-live` continues to work as the local equivalent path and produces compatible evidence under `docs/health/`.
  - README/STATUS counts continue to reconcile with `queries/catalog.json` via the extended drift check.
**Plans**: TBD

---

## Milestone v3.0 - Logan QL Conversion Workbench

Phases 12-16 define and deliver the integrated `webapp/` workbench for converting Splunk SPL, Microsoft Sentinel KQL, Elastic/Lucene/KQL, Sigma/YAML, and OCI passthrough examples into OCI Log Analytics QL. This repository remains the producer of generated command-reference, mapping-pattern, example, and schema artifacts; `webapp/` consumes those artifacts and implements the user-facing editor/output experience.

- [ ] **Phase 12:** Frontend Boundary and Artifact/API Contract
- [ ] **Phase 13:** Official OCI Logan QL Reference Catalog
- [ ] **Phase 14:** Cross-QL Conversion Pattern Library
- [ ] **Phase 15:** Integrated Workbench UX
- [ ] **Phase 16:** Examples, Validation, and Release Gates

### Phase 12: Frontend Boundary and Artifact/API Contract

**Goal**: The milestone has a clear producer/consumer boundary, integrated `webapp/` target, and versioned artifact/API schemas before UI implementation starts.
**Depends on**: Phase 11 planning context; may execute while unresolved v2.0 implementation items remain isolated.
**Requirements**: API-01, API-02, API-03
**Success Criteria** (what must be TRUE):
  1. The integrated `webapp/` target is documented as the maintained UI surface.
  2. `schemas/logan_workbench/` defines versioned JSON schemas for artifact manifest, conversion request, conversion response, command reference, examples, and warnings.
  3. The artifact import path from this repo to `webapp/` is repeatable and documented, with build/startup validation expected in the app.
  4. Sentinel and Sigma workbench examples are sourced through existing converter/mapping paths rather than UI-owned converter generation logic.
**Exit Conditions**:
  - A phase summary names the exact `webapp/` route to implement.
  - Producer-side schema tests pass.
  - UI code added inside this repository stays under `webapp/` and does not duplicate producer logic.
**Plans**: TBD

### Phase 13: Official OCI Logan QL Reference Catalog

**Goal**: The workbench command menu is generated from official OCI Log Analytics documentation with provenance, categories, syntax summaries, and deterministic tests.
**Depends on**: Phase 12
**Requirements**: REFCAT-01, REFCAT-02, REFCAT-03
**Success Criteria** (what must be TRUE):
  1. `scripts/generate_logan_reference_catalog.py` writes `queries/logan_ql_reference_catalog.json` from the OCI query-search and command-reference documentation sources.
  2. Each catalog entry includes command name, category, source URL, retrieved timestamp, syntax summary, and examples or notes where the official page exposes them.
  3. The generated catalog includes at least the core commands needed by the workbench menu: `search`, `stats`, `timestats`, `eval`, `fields`, `where`, `sort`, `top`, `distinct`, `regex`, `lookup`, extraction commands, and clustering-related commands when present in the reference.
  4. Tests fail if required command metadata or provenance is missing, and normal local tests use fixtures rather than live network calls.
**Exit Conditions**:
  - Catalog generation is deterministic for unchanged fixtures.
  - Manual edits to generated catalog output are documented as disallowed.
  - `webapp/` has a documented artifact field map for menu rendering.
**Plans**: TBD

### Phase 14: Cross-QL Conversion Pattern Library

**Goal**: Users can understand how source-query constructs map to OCI Log Analytics QL before the UI exposes arbitrary conversion behavior.
**Depends on**: Phase 13
**Requirements**: XQL-01, XQL-02, XQL-03, DOC-01
**Success Criteria** (what must be TRUE):
  1. `queries/cross_ql_mapping_patterns.json` covers source filters, field references, boolean logic, time windows, aggregation, projection, eval/extend, regex/extraction, lookup/watchlist semantics, joins/correlation, sort/top, and unsupported constructs.
  2. Every pattern includes source language, source construct, OCI Log Analytics QL command mapping, support level, warning behavior, and example references.
  3. `docs/logan_workbench_mapping_guide.md` explains how to map Splunk SPL, Sentinel KQL, Elastic/Lucene/KQL, Sigma/YAML, and generic query constructs to OCI Log Analytics QL.
  4. Lossy or unsupported constructs emit explicit `lossy` or `unsupported` metadata and are never represented as fully supported conversions.
**Exit Conditions**:
  - Pattern tests cover representative constructs for every supported source language.
  - Unsupported examples are tested as blocked or warning-emitting responses.
  - Mapping guide links examples to generated pattern IDs.
**Plans**: TBD

### Phase 15: Integrated Workbench UX

**Goal**: `webapp/` exposes a real converter workbench as the first screen for this capability, backed by generated artifacts from this repo.
**Depends on**: Phase 14
**Requirements**: WB-01, WB-02, DOC-02, QA-03
**Success Criteria** (what must be TRUE):
  1. The `/forge` route provides source language selector, source editor, OCI Log Analytics QL output, explanation panel, command/reference menu, example picker, warnings, and copy/export actions.
  2. The UI consumes generated catalog, pattern, schema, and example artifacts and validates them through `webapp/` TypeScript/Zod boundaries.
  3. Command menu entries and examples provide contextual mapping guidance without turning the first screen into a marketing or static documentation page.
  4. Browser checks cover desktop and mobile layouts, keyboard operation for copy/export, visible warning states, and no incoherent text overlap.
**Exit Conditions**:
  - `webapp/` build, typecheck, lint, and targeted browser tests pass.
  - The workbench can convert or explain all Phase 16 examples through the same UI path.
  - This repo records the `webapp/` artifact import command and verification evidence location.
**Plans**: TBD

### Phase 16: Examples, Validation, and Release Gates

**Goal**: The workbench milestone is backed by realistic, synthetic, tested examples and repeatable release gates across producer artifacts and `webapp/`.
**Depends on**: Phase 15
**Requirements**: WB-03, QA-01, QA-02
**Success Criteria** (what must be TRUE):
  1. `queries/conversion_examples.json` contains 10-20 examples across Splunk SPL, Sentinel KQL, Elastic/Lucene/KQL, Sigma/YAML, and OCI QL passthrough.
  2. Each example includes source query, source language, expected OCI Log Analytics QL, explanation, warnings, support level, and synthetic log shape reference where applicable.
  3. Producer-side tests validate schemas, command catalog, mapping patterns, examples, warnings, and sensitive-value scans.
  4. `webapp/` e2e checks exercise example loading, conversion/explanation rendering, command menu use, warning display, copy/export actions, and responsive layout.
**Exit Conditions**:
  - No workbench artifact contains credentials, OCIDs, public IPs, tenancy names, or unredacted live payloads.
  - `python3 -m pytest` targeted workbench tests pass in this repo.
  - The `webapp/` verification commands pass and are recorded in the handoff.
**Plans**: TBD

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. GSD Brownfield Baseline | 3/3 | Complete | 2026-05-14 |
| 2. Detection Integrity Gates | 3/3 | Complete | 2026-05-14 |
| 3. Sentinel Conversion Backlog | 3/3 | Complete | 2026-05-14 |
| 4. Dashboard and Parser Contract Hardening | 4/4 | Complete | 2026-05-15 |
| 5. Release and Security Automation | 3/3 | Complete | 2026-05-15 |
| 6. KQL Subpackage Extraction and Canonicalizer | 10/10 | Complete | 2026-05-16 |
| 7. Mapping Config Sharding and Collision Lint | 4/4 | Complete | 2026-05-17 |
| 8. Backlog Prioritizer and Cohort Overlay | 3/3 | Complete | 2026-05-17 |
| 9. Operator Parity and Field Mapping Bulk Expansion | 0/? | Not started | - |
| 10. Drift Detector and Synthetic-Hit Promotion Gate | 0/? | Not started | - |
| 11. CI Workflow with PR Dry-Run vs Scheduled-Live Lane Split | 0/? | Not started | - |
| 12. Frontend Boundary and Artifact/API Contract | 0/? | Not started | - |
| 13. Official OCI Logan QL Reference Catalog | 0/? | Not started | - |
| 14. Cross-QL Conversion Pattern Library | 0/? | Not started | - |
| 15. Sibling Workbench UX Integration | 0/? | Not started | - |
| 16. Examples, Validation, and Release Gates | 0/? | Not started | - |

---
*Roadmap created: 2026-05-14*
*Last updated: 2026-05-17 - v3.0 Logan QL Conversion Workbench phases added*
