# Feature Research

**Domain:** Cross-QL conversion workbench for OCI Log Analytics QL
**Researched:** 2026-05-17
**Confidence:** HIGH for table-stakes features and integrated `webapp/` target after the 2026-05-18 user decision

## Feature Landscape

### Table Stakes

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Source language selector | Users need to choose Splunk SPL, Sentinel KQL, Elastic/Lucene/KQL, Sigma/YAML, or OCI QL passthrough. | MEDIUM | Must drive parser, examples, validation, and explanation labels. |
| Source editor and OCI output editor | Converter tools are expected to be paste-in, convert-out workflows. | MEDIUM | Use stable dimensions so editor/output panels do not resize unpredictably. |
| Structured conversion explanation | Users need to know how the target Logan QL was derived. | HIGH | Explanation should map source clauses to OCI commands, fields, and warnings. |
| Official OCI command/reference menu | User explicitly requested a menu updated from official OCI pages. | MEDIUM | Generate from Oracle docs and consume in `webapp/`. |
| Cross-QL mapping guide | Users need general mapping rules, not only examples. | HIGH | Cover filters, fields, boolean logic, time windows, aggregation, projection, eval, regex/extraction, lookup, and correlation limits. |
| Copy/export actions | Converter tools need fast handoff into saved searches, docs, or demos. | LOW | Include copy Logan QL, download JSON, and copy explanation. |
| Warning states for unsupported/lossy constructs | Detection quality depends on explicit limitations. | HIGH | Never silently weaken detections. |
| Example gallery | Users need known-good examples to understand behavior quickly. | MEDIUM | Seed with 10-20 source queries across Sentinel, Splunk, Elastic, Sigma, and OCI QL. |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Official-docs-derived command menu with provenance | Shows the UI is grounded in OCI docs, not stale blog examples. | MEDIUM | Include `source_url`, `retrieved_at`, command name, category, syntax summary, and examples where available. |
| Security-detection-aware mapping explanations | Better than generic syntax translation because it explains semantic gaps. | HIGH | Tie warnings to field mapping, parser readiness, and unsupported source-language operators. |
| Artifact parity with live-validated Sentinel/Sigma paths | Gives the workbench the same semantics as committed detections. | HIGH | UI consumes artifacts from this repo; converters remain producer-side. |
| Real Sentinel-shaped sample logs and Logan QL examples | Supports demos without leaking tenant data. | MEDIUM | Reuse synthetic log patterns and current promoted Sentinel query shapes. |

### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| "Convert anything perfectly" claim | Looks compelling in marketing. | Cross-SIEM semantics are not one-to-one. | Show support levels and warnings per construct. |
| Live OCI validation from the public browser | Confirms parser behavior. | Requires credentials and could leak tenancy context. | Keep live validation explicit, profile-driven, and outside browser storage. |
| LLM-only conversion | Appears flexible for arbitrary syntax. | Non-deterministic and hard to test for detections. | Deterministic patterns first; optional future assist must be clearly labeled. |
| UI-owned command metadata | Fast to hard-code. | Drifts from official OCI pages. | Generated reference artifact from this repo. |

## Feature Dependencies

```
Reference Catalog
    -> Workbench Command Menu
    -> Mapping Guide

Artifact/API Contract
    -> webapp Import
    -> Example Gallery
    -> Frontend Tests

Cross-QL Pattern Library
    -> Conversion Explanation
    -> Warning States
    -> Example Validation
```

### MVP Definition

### Launch With

- [ ] Integrated `webapp/` route selected and documented.
- [ ] Versioned JSON schema for command catalog, mapping patterns, examples, and conversion response.
- [ ] Official OCI command/reference catalog generated from documented Oracle URLs.
- [ ] Workbench UI with source selector, editor, Logan QL output, explanation, command menu, warnings, and copy/export actions.
- [ ] Mapping guide and 10-20 validated examples across the requested source languages.

### Add After Validation

- [ ] Full arbitrary SPL and Elastic parser depth beyond the first supported constructs.
- [ ] Optional API service wrapping producer-side converters.
- [ ] User-provided custom field mapping overlays.

### Future Consideration

- [ ] LLM-assisted explanation mode, clearly separated from deterministic conversion.
- [ ] Live OCI parser validation from a secured server-side integration.
- [ ] Team-shared conversion history and review workflow.

## Competitor Feature Analysis

| Feature | sigconverter.io Pattern | Uncoder.io Pattern | Our Approach |
|---------|--------------------------|--------------------|--------------|
| Source-to-target conversion | Sigma-focused conversion workflow | Multi-platform rule/query conversion | Multi-source workbench focused on OCI Log Analytics QL as the target. |
| Target explanation | Usually secondary to generated output | Varies by target | Make explanation and support level first-class. |
| Reference docs | Tool-owned mapping knowledge | Tool-owned platform templates | Generate OCI command menu from official Oracle docs. |
| Security semantics | Detection-rule oriented | Detection-rule oriented | Tie every warning to field mapping, parser readiness, or unsupported semantics. |

## Sources

- Oracle OCI Log Analytics query search documentation.
- Oracle OCI Log Analytics command reference.
- User-provided comparable tools: sigconverter.io and Uncoder.io.
- Existing repo converter and synthetic-log artifacts.

---
*Feature research for: v3.0 Logan QL Conversion Workbench*
*Researched: 2026-05-17*
