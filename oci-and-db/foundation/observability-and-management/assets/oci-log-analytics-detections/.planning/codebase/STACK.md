---
last_mapped_commit: 671c18eb3203a99666d170682997de48cb43f0f2
mapped_at: 2026-05-14
focus: tech
---

# Stack

## Languages and Runtime

- Python 3 is the primary runtime for conversion, validation, generation, deployment, and tests.
- YAML is used for Sigma-style source rules under `rules/**`.
- JSON is used for generated query artifacts, dashboard inventory, source/field dictionaries, detection-rule specs, Sentinel reports, synthetic-log contracts, and manifests.
- Shell is present for legacy/demo entrypoints such as `SOC_Security_Dashboard.sh`.

## Dependencies

Declared in `requirements.txt`:

- `oci>=2.130.0` for OCI SDK clients.
- `PyYAML>=6.0` for source-rule and mapping parsing.
- `python-dotenv>=1.0.0` for local environment/profile loading.

The tests currently run with `python3 -m pytest -q` even though many tests use stdlib `unittest`.

## Key Scripts

- `scripts/convert_sigma.py` - converts Sigma/YAML source rules into OCI Log Analytics query JSON.
- `scripts/sentinel_conversion_workflow.py` - wraps Sentinel conversion, promotion, reporting, and status checks.
- `scripts/convert_sentinel_kql.py` - lower-level KQL-to-OCL conversion support.
- `scripts/generate_catalog.py` - generates `CATALOG.md` and `queries/catalog.json`.
- `scripts/deploy_dashboard.py` - defines dashboards, validates queries, exports dashboard inventory, and deploys/imports dashboards.
- `scripts/setup_log_sources.py` - creates or updates OCI Log Analytics parsers/sources and field mappings.
- `scripts/generate_dashboard_data.py` and `scripts/generate_test_logs.py` - generate synthetic demo datasets.
- `scripts/ingest_test_data.py` - uploads generated test data to Log Analytics.
- `scripts/release_checklist.py` - runs the local release gates and optional live verification.

## Configuration Files

- `config/sigma_oci_mapping.yaml` - Sigma field/logsource mapping to OCI Log Analytics.
- `config/sentinel_oci_mapping.yaml` - Sentinel conversion table/field mapping allow-list.
- `config/synthetic_log_contracts.json` - expected synthetic dataset/source contracts.
- `config/threat_intel_sources.json` - source-attributed candidate discovery configuration.
- `config/streaming_config.json` - runtime streaming/connectors contract for live ingestion setup.

## Generated Artifact Surfaces

- `queries/catalog.json` - canonical inventory.
- `queries/dashboard_inventory.json` - dashboard/widget/saved-search inventory.
- `queries/content_candidates.json` - discovery and gap-analysis output.
- `queries/log_source_field_dictionary.json` - parser/source/display-field contract.
- `queries/detection_rule_specs.json` - scheduled-search/detection-rule export.
- `queries/octo_apm_workshop_bundle.json` - scoped downstream workshop bundle.
- `queries/sentinel_conversion_report.json` - Sentinel conversion status and failures.
- `queries/manifest.json` - multicloud/export artifact.
- `test_data/manifest.json` - generated synthetic dataset inventory.

## Local Commands

- Tests: `python3 -m pytest -q`
- Rule quality: `python3 scripts/audit_rule_quality.py --report docs/RULE_QUALITY_REPORT.md`
- Catalog: `python3 scripts/generate_catalog.py`
- Dashboard dry-run: `python3 scripts/deploy_dashboard.py --dry-run`
- Release gates: `python3 scripts/release_checklist.py`
