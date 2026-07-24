---
last_mapped_commit: 671c18eb3203a99666d170682997de48cb43f0f2
mapped_at: 2026-05-14
focus: arch
---

# Architecture

## Pattern

The repo is an artifact-producing detection engineering pipeline. It has a source authoring layer, conversion/generation scripts, generated artifact contracts, deployment helpers, synthetic data generators, and validation gates.

## Data Flow

```text
rules/** ------------------------------------> scripts/convert_sigma.py
                                                 |
                                                 +--> queries/*.json
                                                 +--> queries/apps/*.json

official Sentinel corpus + mapping config ----> scripts/sentinel_conversion_workflow.py
                                                 |
                                                 +--> queries/sentinel/*.json
                                                 +--> queries/sentinel_conversion_report.json

queries/** + dashboard definitions -----------> scripts/generate_catalog.py
queries/** + dashboard definitions -----------> scripts/deploy_dashboard.py
queries/** -----------------------------------> scripts/export_for_multicloud.py
parser mappings + synthetic contracts --------> scripts/field_dictionary.py
```

## Layers

- Source authoring: `rules/**`, curated `queries/apps/**`, curated `queries/hunting/**`.
- Conversion: `scripts/convert_sigma.py`, `scripts/convert_sentinel_kql.py`, `scripts/sentinel_conversion_workflow.py`.
- Inventory: `scripts/generate_catalog.py`, `scripts/export_for_multicloud.py`, `scripts/field_dictionary.py`, `scripts/detection_rule_creator.py`.
- Deployment: `scripts/setup_log_sources.py`, `scripts/deploy_dashboard.py`, `scripts/setup_streaming_pipeline.py`, `scripts/ingest_test_data.py`.
- Verification: `scripts/test_*.py`, `scripts/audit_rule_quality.py`, `scripts/validate_synthetic_logs.py`, `scripts/release_checklist.py`, `scripts/verify_deployed_dashboards.py`.
- Documentation: `README.md`, `STATUS.md`, `docs/**`, `CATALOG.md`, `.planning/**`.

## Entry Points

- Local validation: `python3 -m pytest -q`
- Release validation: `python3 scripts/release_checklist.py`
- Dashboard inventory/dry-run: `python3 scripts/deploy_dashboard.py --export-inventory` and `--dry-run`
- Sentinel status: `python3 scripts/sentinel_conversion_workflow.py status --json --strict`
- Rule quality: `python3 scripts/audit_rule_quality.py --report docs/RULE_QUALITY_REPORT.md`

## Core Invariants

- `queries/catalog.json` is canonical for counts.
- `queries/dashboard_inventory.json` is generated from dashboard definitions.
- `queries/sentinel/**` contains only promoted live-validation-passed Sentinel conversions.
- `logandetectionqueries/` and `logandetectionrules/` are legacy empty directories.
- `SOC Application Logs` is the supported source for app/browser/APM analytics.
- Tenant-specific values must remain placeholders or environment-provided values.

## GSD Fit

GSD phases should treat generated artifacts as first-class deliverables. A phase is not done when code changes pass tests only; generated inventory/docs must also be reconciled when the code path changes counts, dashboards, fields, or manifests.
