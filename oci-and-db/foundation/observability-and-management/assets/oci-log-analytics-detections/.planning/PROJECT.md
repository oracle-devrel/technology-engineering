# OCI Log Analytics Detections

## What This Is

This is a brownfield detection-content, dashboard-deployment, and Forge webapp repository for Oracle Cloud Infrastructure Log Analytics. It converts Sigma/YAML and live-validated Microsoft Sentinel content into OCI Log Analytics Query Language, maintains curated hunting and app analytics, generates synthetic demo data, deploys OCI Management Dashboards, and ships the integrated Forge workbench for cross-QL conversion into OCI Log Analytics QL.

The repo is the canonical detection, dashboard, and workbench artifact producer for the integrated `webapp/` and downstream tools such as `mcp-oci-logan-server`; consumers should read generated artifacts from this repo rather than duplicate generation logic.

## Core Value

Every committed detection, query, dashboard, parser mapping, and generated artifact must remain deployable and verifiable against OCI Log Analytics without leaking tenant-specific data.

## Current Milestone: v3.0 Logan QL Conversion Workbench

**Goal:** Maintain an integrated web workbench under `webapp/` that converts Splunk SPL, Microsoft Sentinel KQL, Elastic/Lucene/KQL, Sigma/YAML, and OCI passthrough examples into OCI Log Analytics QL while this repository remains the canonical producer of conversion/reference artifacts.

**Target features:**
- Versioned artifact/API contract for the integrated frontend workbench that consumes generated content from this repo instead of duplicating conversion logic.
- Official OCI Log Analytics command/reference catalog generated from Oracle documentation and exposed to the frontend as the workbench command menu.
- Cross-QL mapping pattern library that explains how filters, fields, boolean logic, time windows, aggregation, projection, eval, regex/extraction, lookups, joins/correlation, and unsupported semantics map to OCI Log Analytics QL.
- Source selector, source editor, OCI Logan QL output, explanation panel, examples, warnings, and copy/export actions in `webapp/`.
- 10-20 validated conversion examples using synthetic Sentinel/OCI-shaped logs and no tenant-specific data.
- Producer-side schema/example tests plus `webapp/` build, typecheck, lint, accessibility, and browser acceptance gates.

**Phase numbering:** continues from v2.0 - starts at Phase 12.

## Requirements

### Validated

- [x] Sigma/YAML authoring layer exists under `rules/**` with 454 source rules and quality audit coverage.
- [x] OCI query artifacts are generated and cataloged under `queries/**`, with `queries/catalog.json` as the canonical machine-readable inventory.
- [x] Microsoft Sentinel conversion workflow promotes only live OCI parser-passing queries into `queries/sentinel/**`.
- [x] Dashboard inventory is generated from `scripts/deploy_dashboard.py` and currently covers 29 dashboards and 438 widgets.
- [x] Synthetic log generation and parser/source setup support SOC security, app/APM, WAF, VCN, firewall, and multicloud-health demo paths.
- [x] Local tests currently pass with `244 passed, 5 skipped, 2 subtests passed`.

### Active

- [ ] Keep GSD planning state current for every substantial development phase.
- [ ] Maintain zero rule-quality audit findings across source rules and generated Sigma queries.
- [ ] Keep catalog, dashboard inventory, manifest, field dictionary, detection-rule specs, and docs synchronized after content changes.
- [ ] Improve Sentinel conversion coverage by triaging local validation failures, field/table mapping gaps, and live validation failures.
- [ ] Harden release evidence so local gates and optional live verification can be run consistently before demos or deployments.
- [ ] Preserve the Octo APM workshop bundle contract for downstream deployment from `octo-apm-demo`.
- [ ] Carry forward open v2.0 Sentinel KQL parity items without weakening the live parser validation gate.
- [ ] Generate official-docs-derived OCI Log Analytics command/reference artifacts for the v3.0 workbench.
- [ ] Generate cross-QL mapping patterns, explanations, warnings, and examples for Splunk, Sentinel, Elastic/Lucene/KQL, Sigma, and OCI QL.
- [ ] Define and validate a versioned producer/consumer contract for the integrated frontend workbench.

### Out of Scope

- Duplicating query generation or dashboard deployment logic in the frontend - `webapp/` and downstream projects consume this repo's generated artifacts.
- Hand-authoring promoted Sentinel JSON under `queries/sentinel/**` - use the converter and live-validation workflow.
- Hand-authoring content in `logandetectionqueries/` or `logandetectionrules/` - they are legacy empty directories.
- Committing public IPs, OCIDs, tenancy names, credentials, API tokens, or profile-specific values.
- Creating OCI alarms or Terraform applies by default from detection-rule specs - specs remain metadata/export artifacts unless explicitly requested.

## Context

- Primary language is Python. The repo uses stdlib `unittest` plus pytest-compatible tests under `scripts/test_*.py`.
- Runtime dependencies are minimal: `oci`, `PyYAML`, and `python-dotenv` in `requirements.txt`.
- Source content surfaces:
  - `rules/**` - source Sigma/YAML rules.
  - `queries/*.json` and generated `queries/apps/*.json` - Sigma-derived OCI saved-search queries.
  - `queries/sentinel/*.json` - Microsoft Sentinel conversions that passed live OCI parser validation.
  - `queries/apps/*.json` and `queries/hunting/*.json` - curated app/hunting analytics.
- Generated contracts:
  - `queries/catalog.json`
  - `queries/dashboard_inventory.json`
  - `queries/content_candidates.json`
  - `queries/log_source_field_dictionary.json`
  - `queries/detection_rule_specs.json`
  - `queries/octo_apm_workshop_bundle.json`
  - `queries/sentinel_conversion_report.json`
  - `queries/manifest.json`
  - Proposed v3.0 workbench contracts:
    - `queries/logan_ql_reference_catalog.json`
    - `queries/cross_ql_mapping_patterns.json`
    - `queries/conversion_examples.json`
    - `schemas/logan_workbench/*.schema.json`
  - `test_data/manifest.json`
- Existing project-specific Claude guidance lives in `CLAUDE.md`; Codex should read `AGENTS.md` and `.planning/**` going forward.

## Constraints

- **OCI Log Analytics compatibility**: Generated OCL must avoid unsupported functions and parser-invalid field usage because deployment validation blocks dashboard import.
- **Source-of-truth discipline**: `rules/**` and converter configs drive generated source-derived queries; generated artifacts should not be patched manually except for curated app/hunting surfaces.
- **Live validation boundary**: Sentinel promotion requires live OCI parser validation; failed candidates stay in `queries/sentinel_conversion_report.json`.
- **Demo safety**: Committed artifacts must use placeholders and redaction for tenant-specific values.
- **Dirty worktree reality**: This repo often has broad generated changes. Future agents must isolate their own edits and avoid reverting unrelated work.
- **Dashboard layout**: Widget placement must use `scripts/deploy_dashboard.py:resolve_widget_layout()` and 12-column metadata; do not hand-author imported row/column placement.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use `.planning/` as the GSD project state root | Enables GSD phase planning, review, verification, and session continuity for this brownfield repo | Pending |
| Treat `queries/catalog.json` as canonical inventory | Avoids stale hand-maintained counts and aligns README/STATUS with generated content | Good |
| Move the Forge UI into `webapp/` | The user selected this repo as the long-term project and retired the old sibling app as the source of truth | Good |
| Promote Sentinel content only after live OCI parser validation | Prevents parser-invalid KQL conversions from becoming dashboard or saved-search assets | Good |
| Keep GSD `commit_docs` enabled but do not auto-commit in dirty worktrees | Planning docs should be tracked, but commits must not include unrelated generated changes | Pending |
| Plan v3.0 as an integrated frontend workbench backed by generated artifacts | User moved the webapp into this long-term repo; the generated artifacts remain the producer boundary | Good |
| Generate the OCI command menu from official Oracle docs | User requested the menu be updated from official OCI pages, so frontend menu data must carry source provenance | Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `$gsd-transition`):
1. Requirements invalidated? Move to Out of Scope with reason.
2. Requirements validated? Move to Validated with phase reference.
3. New requirements emerged? Add to Active.
4. Decisions to log? Add to Key Decisions.
5. "What This Is" still accurate? Update if drifted.

**After each milestone** (via `$gsd-complete-milestone`):
1. Full review of all sections.
2. Core Value check - still the right priority?
3. Audit Out of Scope - reasons still valid?
4. Update Context with current state.

## GSD Usage

- Start phase work with `$gsd-plan-phase <phase-number>`.
- Use `$gsd-audit-fix` for audit-to-fix loops when there are concrete findings.
- Use `$gsd-map-codebase` after major structural changes to refresh `.planning/codebase/**`.
- Keep `.planning/STATE.md` updated after major sessions and phase transitions.

---
*Last updated: 2026-05-17 for v3.0 Logan QL Conversion Workbench milestone*
