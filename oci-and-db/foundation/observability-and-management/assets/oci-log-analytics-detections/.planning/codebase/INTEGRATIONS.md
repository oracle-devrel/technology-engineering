---
last_mapped_commit: 671c18eb3203a99666d170682997de48cb43f0f2
mapped_at: 2026-05-14
focus: tech
---

# Integrations

## Oracle Cloud Infrastructure

Primary integration is OCI Log Analytics through the OCI Python SDK:

- `scripts/oci_config.py` centralizes profile, tenancy, compartment, namespace, and client helpers.
- `scripts/setup_log_sources.py` manages Log Analytics sources, parsers, fields, and parser mappings.
- `scripts/deploy_dashboard.py` validates Log Analytics queries and imports OCI Management Dashboards.
- `scripts/ingest_test_data.py` uploads generated datasets.
- `scripts/setup_streaming_pipeline.py` configures streams and service connectors for live ingestion.
- `scripts/verify_deployed_dashboards.py` runs live dashboard/widget validation.

## OCI Management Dashboards

Dashboard definitions live in code in `scripts/deploy_dashboard.py`. Generated inventory is written to `queries/dashboard_inventory.json`.

Important contract:

- Widget layout should be driven by visualization metadata and `resolve_widget_layout()`.
- Dashboard saved-search widgets default to scoped lookbacks where needed for demo visibility.
- Import should be preceded by local dry-run/query validation.

## Sigma

Source rules under `rules/**` follow Sigma-style YAML and are converted through `scripts/convert_sigma.py`.

Local SigmaHQ cache exists under `.sigmahq/` and is used for synchronization and coverage work. Treat it as an input cache, not a project output surface.

## Microsoft Sentinel

Sentinel content comes from an Azure Sentinel corpus cache and converter workflow:

- `.sentinel/Azure-Sentinel/` - local corpus cache.
- `scripts/sync_sentinel_kql.py` - sync support.
- `scripts/convert_sentinel_kql.py` - conversion implementation.
- `scripts/sentinel_conversion_workflow.py` - local/promote/refresh/page/triage/status wrapper.
- `queries/sentinel/**` - only live OCI parser-passing promoted query artifacts.
- `queries/sentinel_conversion_report.json` - source of truth for skipped, failed, and promoted candidates.

## Webapp and Downstream Consumers

This repo produces artifacts for its integrated webapp and downstream projects:

- `webapp/` consumes the Logan workbench artifacts, catalog, dashboard inventory, and test-data manifest.
- `mcp-oci-logan-server` should consume generated query/dashboard contracts.
- `octo-apm-demo` consumes `queries/octo_apm_workshop_bundle.json` and scoped deployment assets.

UI and downstream projects must not duplicate query generation or OCI dashboard deployment logic.

## External Research Sources

Source-attributed candidate discovery and documentation references include:

- SigmaHQ rule corpus.
- Microsoft Sentinel official content.
- MITRE ATT&CK metadata embedded in rules.
- Atomic Red Team mappings via `config/art_index.csv` and `scripts/map_atomic_tests.py`.
- FreeLabFriday, MELTS, BLUELIGHT/APT37, and related source-attributed hunt content as documented in README/STATUS.
