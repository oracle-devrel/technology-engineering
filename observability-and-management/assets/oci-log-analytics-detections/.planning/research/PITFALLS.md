# Pitfalls Research

**Domain:** SIEM query conversion workbench for OCI Log Analytics QL
**Researched:** 2026-05-17
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Stale OCI Command Menu

**What goes wrong:**
The UI ships a menu that no longer matches Oracle's Log Analytics command reference.

**Why it happens:**
Command metadata is copied into React components by hand and never reconciled.

**How to avoid:**
Generate the command catalog from official Oracle pages, keep source URLs and retrieval timestamps, and fail tests when required fields are missing.

**Warning signs:**
Menu entries have no provenance, no schema, or no generated artifact.

**Phase to address:**
Phase 13.

### Pitfall 2: Silent Semantic Loss

**What goes wrong:**
A source query converts to OCI QL that looks valid but weakens the detection.

**Why it happens:**
Constructs such as joins, dynamic bags, command-line parsing, regex differences, or watchlists are simplified without a warning.

**How to avoid:**
Every pattern must carry a support level and explanation. Lossy or unsupported constructs must emit warnings or block conversion.

**Warning signs:**
Conversion output exists but the response has no warnings, no source-to-target trace, or no support-level metadata.

**Phase to address:**
Phase 14.

### Pitfall 3: Repo Boundary Drift

**What goes wrong:**
The frontend owns its own conversion logic and diverges from this repo's generated artifacts.

**Why it happens:**
UI implementation starts before the artifact/API contract is defined.

**How to avoid:**
Start with Phase 12. Define schemas, artifact ownership, import path, and test responsibilities before frontend implementation.

**Warning signs:**
TypeScript conversion rules appear in `webapp/` without a matching generated artifact or producer-side test.

**Phase to address:**
Phase 12.

### Pitfall 4: Demo Data Leaks Tenant Context

**What goes wrong:**
Examples include OCIDs, public IPs, tenant-specific names, or unredacted live payloads.

**Why it happens:**
Useful live logs are copied into examples to make the demo realistic.

**How to avoid:**
Use synthetic Sentinel-shaped and OCI-shaped logs only. Extend sensitive-value scans to workbench artifacts and examples.

**Warning signs:**
Example files contain OCI IDs, public routable IPs, compartment names, tenancy suffixes, or unreviewed raw logs.

**Phase to address:**
Phase 16.

### Pitfall 5: Converter UI Looks Useful But Cannot Be Tested

**What goes wrong:**
The workbench is visually complete, but no gate proves the examples, warnings, menu, and output stay consistent.

**Why it happens:**
Frontend work is treated as a static page instead of a contract-consuming tool.

**How to avoid:**
Require producer-side schema/example tests and `webapp/` build/type/lint/e2e tests before milestone completion.

**Warning signs:**
No fixture-driven examples, no browser test path, no schema validation in `webapp/` import code.

**Phase to address:**
Phase 16.

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Inline menu data in UI | Fast first screen | Docs drift and impossible provenance | Never for final milestone scope. |
| Regex-only query parsing | Fast examples | Breaks nested clauses and quoted strings | Only for clearly labeled demo examples, not production conversion. |
| One artifact blob | Fewer files | Hard to validate or version independently | Acceptable only for an initial spike; Phase 12 should split schemas. |
| UI-only warnings | Easy to render | No producer-side traceability | Never; warnings belong in conversion response artifacts. |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Oracle docs | Runtime scraping from browser | Offline generator with fixture tests and provenance fields. |
| Sibling frontend | Copy artifacts manually | Document a repeatable import/build step. |
| Existing converters | Reimplement in TypeScript | Wrap or consume producer-side converter outputs. |
| Examples | Store live payloads | Use synthetic, redacted, schema-valid samples. |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Landing-page-first design | User cannot immediately convert a query. | Open directly to the workbench. |
| Huge explanatory text blocks | Slows operator workflows. | Use compact panels, examples, and contextual warnings. |
| Output without mapping trace | Users cannot trust the conversion. | Pair every output with source-to-target explanation. |
| Menu detached from editor | Command reference feels like documentation, not a tool. | Let menu entries insert examples or filter mapping guidance. |

## Looks Done But Is Not Checklist

- [ ] Command menu exists but has no official-doc provenance.
- [ ] Example conversions render but are not schema-tested.
- [ ] Warnings show visually but are not part of the conversion response.
- [ ] Sibling frontend imports static JSON without runtime validation.
- [ ] Workbench uses real-looking logs that have not passed sensitive-value scan.
- [ ] Mobile layout hides warnings or copy/export controls.

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Repo boundary drift | Phase 12 | Schemas and import contract exist before UI implementation. |
| Stale OCI menu | Phase 13 | Generated catalog includes source URLs and tests. |
| Silent semantic loss | Phase 14 | Pattern library marks lossy/unsupported constructs. |
| Untestable UI | Phase 15 and Phase 16 | Sibling e2e path covers editor, menu, examples, warnings, copy/export. |
| Tenant data leakage | Phase 16 | Sensitive-value scan covers workbench artifacts and examples. |

## Sources

- Oracle OCI Log Analytics query search documentation.
- Oracle OCI Log Analytics command reference.
- Existing project hard rules in `AGENTS.md` and `.planning/PROJECT.md`.
- Prior Sentinel conversion lessons from v2.0 planning state.

---
*Pitfalls research for: v3.0 Logan QL Conversion Workbench*
*Researched: 2026-05-17*
