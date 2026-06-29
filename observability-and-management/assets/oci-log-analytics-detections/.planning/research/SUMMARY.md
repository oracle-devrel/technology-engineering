# Project Research Summary

**Project:** OCI Log Analytics Detections
**Domain:** Cross-QL conversion workbench for OCI Log Analytics QL
**Researched:** 2026-05-17
**Confidence:** HIGH for artifact boundary, OCI reference needs, and integrated `webapp/` target after the 2026-05-18 user decision

## Executive Summary

Milestone v3.0 adds a Logan QL conversion workbench without moving this repository away from its producer role. The current architecture is an integrated `webapp/` frontend that consumes versioned artifacts generated here: official-docs-derived OCI command metadata, cross-QL mapping patterns, conversion examples, and request/response schemas.

The first implementation risk is semantic drift. A converter that produces plausible OCI Log Analytics QL but hides unsupported or lossy source constructs would be dangerous for detection content. The milestone should make support levels, warnings, and source-to-target explanations part of the artifact contract before frontend implementation begins.

The second implementation risk is stale reference data. The user explicitly requested an OCI command menu updated from official OCI pages, so command metadata must be generated with source URLs and timestamps, tested with fixtures, and consumed by `webapp/` rather than hand-authored in React.

## Key Findings

### Recommended Stack

Use this repo's Python scripts for producer-side artifacts and the integrated Next.js/React/TypeScript stack under `webapp/` for the frontend.

**Core technologies:**
- Python generators: create command catalog, mapping patterns, examples, and schemas.
- JSON Schema plus Zod: enforce the producer/consumer artifact boundary.
- Next.js/React/TypeScript: implement the integrated workbench UI.
- Playwright or Browser checks: verify desktop/mobile workbench behavior in `webapp/`.

### Expected Features

**Must have:**
- Source language selector for Splunk SPL, Sentinel KQL, Elastic/Lucene/KQL, Sigma/YAML, and OCI Logan QL.
- Source editor, OCI output panel, copy/export controls, and warning states.
- Official OCI Log Analytics command menu generated from Oracle docs.
- Mapping explanation that traces source clauses to OCI commands, fields, and support levels.
- 10-20 validated examples across the requested source languages.

**Should have:**
- Command menu entries that can filter mapping guidance or insert examples.
- Security-detection-aware warnings tied to field mapping and parser readiness.
- Import/build gates that prove `webapp/` artifacts are current.

**Defer:**
- Live OCI parser validation from the browser.
- LLM-assisted conversion or explanation.
- Team-shared conversion history.

### Architecture Approach

Keep conversion/reference production in this repo and UI interaction in `webapp/`. This repo should produce `queries/logan_ql_reference_catalog.json`, `queries/cross_ql_mapping_patterns.json`, `queries/conversion_examples.json`, and `schemas/logan_workbench/*.schema.json`. The integrated frontend validates and renders those artifacts, and any arbitrary-query conversion path must be defined through a request/response contract that can wrap producer-side converters.

### Critical Pitfalls

1. **Stale OCI command menu:** Generate from official docs with provenance and tests.
2. **Silent semantic loss:** Mark each mapping as supported, warning, lossy, or unsupported.
3. **Repo boundary drift:** Define schemas and ownership before UI implementation.
4. **Tenant data leakage:** Use synthetic logs only and scan examples.
5. **Untestable UI:** Require producer artifact tests plus `webapp/` build/type/lint/e2e gates.

## Implications for Roadmap

### Phase 12: Frontend Boundary and Artifact/API Contract

**Rationale:** The milestone spans producer scripts and `webapp/`, so ownership and schemas must come first.
**Delivers:** Integrated target decision, artifact names, JSON schemas, conversion request/response contract, and import strategy.
**Avoids:** Repo boundary drift.

### Phase 13: Official OCI Logan QL Reference Catalog

**Rationale:** The command menu is a first-class user requirement and must not be hand-authored.
**Delivers:** Generated command catalog from official Oracle pages with provenance and tests.
**Avoids:** Stale OCI reference data.

### Phase 14: Cross-QL Conversion Pattern Library

**Rationale:** Users asked for mapping from any QL to OCI Log Analytics QL; this requires deterministic pattern coverage before UI polish.
**Delivers:** Mapping patterns for Splunk, Sentinel, Elastic/Lucene/KQL, Sigma, and OCI passthrough with support levels and explanations.
**Avoids:** Silent semantic loss.

### Phase 15: Integrated Workbench UX

**Rationale:** Once artifacts are stable, `webapp/` can implement the real workbench as the first screen.
**Delivers:** Editor, output, command menu, explanation panel, example picker, warnings, and copy/export actions.
**Avoids:** Landing-page-first or documentation-only implementation.

### Phase 16: Examples, Validation, and Release Gates

**Rationale:** The milestone is not production-ready until examples and artifact/UI contracts are tested end to end.
**Delivers:** 10-20 validated conversions, producer tests, `webapp/` gates, sensitive-value scans, and handoff docs.
**Avoids:** Demo-only behavior and data leakage.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Integrated `webapp/` stack is known; producer-side Python boundary is already established. |
| Features | HIGH | User request and comparable tools define the expected workbench surface clearly. |
| Architecture | HIGH | Repo hard rules require UI/API consumers to consume generated artifacts. |
| Pitfalls | HIGH | Prior Sentinel conversion work exposed the main risks around semantic loss, live validation, and synthetic data. |

**Overall confidence:** HIGH.

## Gaps to Address

- **Integrated target:** Phase 12 now records `webapp/` as the maintained UI surface.
- **Arbitrary SPL/Elastic depth:** Phase 14 must define first supported constructs and warnings rather than promising complete language parity.
- **Docs scraping mechanics:** Phase 13 should fixture official docs pages so local tests are deterministic.

## Sources

### Primary

- Oracle OCI Log Analytics query search documentation.
- Oracle OCI Log Analytics command reference.
- Project artifact boundary rules in `AGENTS.md` and `.planning/PROJECT.md`.

### Secondary

- `webapp/package.json` for the integrated frontend stack.
- User-provided comparable tools: sigconverter.io and Uncoder.io.

---
*Research completed: 2026-05-17*
*Ready for roadmap: yes*
