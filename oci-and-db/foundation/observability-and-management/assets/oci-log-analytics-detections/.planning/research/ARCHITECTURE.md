# Architecture Research

**Domain:** Integrated web frontend backed by OCI Log Analytics conversion artifacts
**Researched:** 2026-05-17
**Confidence:** HIGH for repository boundary and integrated `webapp/` route placement after the 2026-05-18 user decision

## Standard Architecture

```
oci-log-analytics-detections
  |
  | generates
  v
queries/logan_ql_reference_catalog.json
queries/cross_ql_mapping_patterns.json
queries/conversion_examples.json
schemas/logan_workbench/*.schema.json
  |
  | consumed by server-side artifact loaders
  v
webapp/
  |
  +-- source editor
  +-- OCI Logan QL output
  +-- explanation panel
  +-- official OCI command menu
  +-- examples and warnings
```

## Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| Reference catalog generator | Fetch or parse official OCI docs into command metadata | Python script in this repo with fixture-backed tests and provenance fields. |
| Cross-QL pattern library | Describe how source constructs map to OCI Log Analytics QL | Generated JSON plus human-readable docs from mapping inputs. |
| Conversion response schema | Define request/response shape for arbitrary source queries | JSON Schema and TypeScript/Zod equivalent in `webapp/`. |
| Integrated workbench UI | Present editor, output, command menu, examples, explanations, and warnings | Next.js route under `webapp/app/(dashboard)/forge/page.tsx`. |
| Validation gates | Prove artifacts and UI examples remain consistent | Python tests in this repo; build/type/lint/e2e in `webapp/`. |

## Recommended Project Structure

Producer-side additions in this repo:

```
scripts/
  generate_logan_reference_catalog.py
  generate_cross_ql_patterns.py
  test_logan_reference_catalog.py
  test_cross_ql_patterns.py
queries/
  logan_ql_reference_catalog.json
  cross_ql_mapping_patterns.json
  conversion_examples.json
schemas/
  logan_workbench/
    artifact.schema.json
    conversion_request.schema.json
    conversion_response.schema.json
docs/
  logan_workbench_mapping_guide.md
```

Integrated `webapp/` additions:

```
webapp/
  app/(dashboard)/forge/page.tsx
components/
  logan-workbench/
    source-editor.tsx
    output-panel.tsx
    command-menu.tsx
    explanation-panel.tsx
    examples-panel.tsx
lib/
  logan-workbench/
    artifacts.ts
    conversion-client.ts
    schemas.ts
tests/
  logan-workbench.spec.ts
```

## Architectural Patterns

### Producer/Consumer Artifact Contract

**What:** This repo emits versioned JSON artifacts and schemas; `webapp/` imports and validates them.

**Trade-offs:** Static artifacts are deterministic and easy to test, but arbitrary pasted-query conversion may eventually need a service wrapper around producer-side converters.

### Support-Level Mapping

**What:** Every conversion pattern is labeled as `supported`, `supported_with_warning`, `lossy`, or `unsupported`.

**Trade-offs:** Users see limitations upfront. It requires more metadata than simple string templates, but avoids silent detection corruption.

### Docs-Derived Menu

**What:** Command menu data is generated from official OCI documentation URLs, not hand-authored in the UI.

**Trade-offs:** The generator must tolerate docs page shape changes. Tests should use saved fixtures so normal builds do not require network access.

## Data Flow

### Artifact Build Flow

```
Oracle docs + mapping config + converter examples
    -> Python generators
    -> JSON artifacts + schemas + docs
    -> Python artifact tests
    -> webapp import/build/e2e tests
```

### User Conversion Flow

```
User selects source language
    -> pastes source query
    -> converter/pattern engine returns Logan QL + explanation + warnings
    -> user copies/exports OCI QL and evidence
```

## Integration Points

| Boundary | Communication | Notes |
|----------|---------------|-------|
| This repo -> `webapp/` | Versioned JSON artifacts and schemas | No duplicate converter generation in the frontend. |
| OCI docs -> reference catalog | Official documentation URLs | Store source URL and retrieval timestamp for each generated catalog. |
| Existing Sentinel converter -> workbench examples | Generated fixtures | Promoted Sentinel semantics must continue to flow through converter/live-validation workflow. |
| Synthetic logs -> examples | Redacted synthetic fixtures | Examples must use real Sentinel/OCI-shaped fields without tenant data. |

## Anti-Patterns

### Frontend Forks the Converter

**What people do:** Rebuild Sentinel/Sigma conversion in TypeScript for convenience.
**Why it is wrong:** Semantics drift from this repo's live-validated artifacts.
**Do this instead:** Define an artifact/API contract that wraps or consumes producer-side conversion logic.

### Menu Is a Static Design Asset

**What people do:** Hand-type OCI commands into React components.
**Why it is wrong:** It breaks the user's requirement to stay aligned with official OCI pages.
**Do this instead:** Generate and validate the menu from docs-derived artifacts.

### Examples Are Only Pretty Strings

**What people do:** Include sample conversions without tests.
**Why it is wrong:** The UI can demonstrate invalid Logan QL.
**Do this instead:** Test examples against schemas, canonical formatting, and converter support levels.

## Sources

- Oracle OCI Log Analytics query search documentation.
- Oracle OCI Log Analytics command reference.
- `.planning/PROJECT.md` and repo artifact boundary rules.
- `webapp/package.json`.

---
*Architecture research for: v3.0 Logan QL Conversion Workbench*
*Researched: 2026-05-17*
