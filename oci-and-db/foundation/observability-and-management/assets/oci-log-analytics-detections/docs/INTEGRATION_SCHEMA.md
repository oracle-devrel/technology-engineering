# Integration Schema

Date: 2026-05-18

This document defines the generated artifact contract consumed by the integrated `webapp/` Forge UI and downstream integrations. Generated files should be treated as read-only inputs by UI/API consumers.

## Artifact Contract

| Artifact | Owner | Purpose | Generator |
|----------|-------|---------|-----------|
| `queries/catalog.json` | Detections repo | Canonical inventory, counts, severity, MITRE/STIG coverage, app queries, and hunting queries | `scripts/generate_catalog.py` |
| `queries/dashboard_inventory.json` | Detections repo | OCI dashboard, widget, saved-search, query-file, and visualization inventory | `scripts/deploy_dashboard.py --export-inventory` |
| `queries/content_candidates.json` | Detections repo | Threat-intel, gap-analysis, and curated workflow candidate inventory | `scripts/content_discovery.py` |
| `queries/log_source_field_dictionary.json` | Detections repo | Parser/source/display-field contract with raw paths, examples, source ownership, and query usage | `scripts/field_dictionary.py` |
| `queries/detection_rule_specs.json` | Detections repo | Scheduled-search detection-rule eligibility specs and metadata-only alarm templates | `scripts/detection_rule_creator.py --write-default` |
| `queries/octo_apm_workshop_bundle.json` | Detections repo | Variable-safe Octo APM workshop slice: dashboard widgets, scoped queries, required fields, synthetic data file, and deployable detection-rule specs | `scripts/octo_apm_workshop.py --export-bundle` |
| `queries/sentinel_conversion_report.json` | Detections repo | Microsoft Sentinel conversion report with attempted candidates, promoted/skipped counts, skip reasons, upstream attribution, and live-validation status | `scripts/sentinel_conversion_workflow.py promote --top all --timeout 20` |
| `queries/logan_ql_reference_catalog.json` | Detections repo | Official-docs-derived OCI Log Analytics command menu consumed by `webapp/` | `scripts/generate_logan_workbench_artifacts.py` |
| `queries/cross_ql_mapping_patterns.json` | Detections repo | Cross-QL mapping pattern library for Sigma, Sentinel KQL, Splunk SPL, Elastic/Lucene/KQL, and OCI passthrough | `scripts/generate_logan_workbench_artifacts.py` |
| `queries/conversion_examples.json` | Detections repo | Validated example conversions shown in the Forge workbench | `scripts/generate_logan_workbench_artifacts.py` |
| `docs/sentinel_converter.html` | Detections repo | Static web review page summarizing Sentinel conversion status, dashboard coverage, top skip reasons, and redacted live-validation failures | `scripts/sentinel_conversion_workflow.py page` |
| `queries/manifest.json` | Detections repo | Export/integration payload for downstream platforms | `scripts/export_for_multicloud.py --manifest-only` |
| `test_data/manifest.json` | Detections repo | Generated synthetic dataset counts | `scripts/generate_test_logs.py` and dataset generators |

## `queries/dashboard_inventory.json`

Top-level shape:

```json
{
  "version": "1.0",
  "generated_at": "2026-05-12T00:00:00.000000+00:00",
  "source": "scripts/deploy_dashboard.py:DASHBOARDS",
  "summary": {
    "total_dashboards": 29,
    "total_widgets": 441,
    "advanced_visualization_widgets": 107,
    "visualization_types": {
      "bar": 4,
      "hbar": 1,
      "line": 9,
      "link": 11,
      "map": 2,
      "summary_table": 66,
      "table": 334,
      "tile": 14
    },
    "levels": {
      "critical": 125,
      "high": 191,
      "informational": 20,
      "low": 11,
      "medium": 94
    }
  },
  "dashboards": []
}
```

Dashboard record:

```json
{
  "name": "SOC: Browser Attack Detection Dashboard",
  "description": "Browser-side attack detection using SOC Application Logs...",
  "widget_count": 13,
  "widgets": []
}
```

Widget record:

```json
{
  "dashboard_name": "SOC: Browser Attack Detection Dashboard",
  "dashboard_index": 15,
  "widget_index": 0,
  "title": "APM: Total Browser Attacks (24h)",
  "query_file": "apps/apm_total_attacks_kpi.json",
  "query_title": "APM: Total Browser Attacks (24h)",
  "description": "Total browser-side attack events...",
  "level": "informational",
  "type": "curated",
  "sigma_id": "",
  "tags": ["apm", "browser", "kpi"],
  "logsource": {
    "product": "application",
    "service": "soc_application_logs"
  },
  "mitre_attack": {
    "tactics": ["initial_access"],
    "techniques": ["T1190"]
  },
  "visualization_type": "tile",
  "visualization_options": {},
  "layout": {
    "width": 3,
    "height": 3
  },
  "time_selection": {
    "timePeriod": "l21d"
  },
  "ask_ai_prompts": [],
  "advanced_visualization": true,
  "drilldowns": [
    {
      "type": "log_explorer_field_pivot",
      "field": "Trace ID",
      "label": "Pivot by Trace ID"
    }
  ],
  "dashboard_quality": {
    "score": 100,
    "checks": {
      "no_overlap": true,
      "supported_visualization": true,
      "widget_returns_rows_in_cap": "not_run",
      "field_contract_coverage": "not_evaluated",
      "visualization_task_fit": "not_scored"
    }
  }
}
```

Required dashboard inventory invariants:

- Every `query_file` is relative to `queries/`.
- Every `query_file` must exist before the artifact is written.
- `query_title` must equal the referenced query JSON `title`.
- `visualization_type` must equal the resolved dashboard metadata from the referenced query, including widget overrides.
- `layout` must contain resolved positive integer `width` and `height`; widget placement is derived from the resolved layout on a 12-column grid.
- `advanced_visualization` is true for `bar`, `hbar`, `line`, `link`, `map`, `pie`, `summary_table`, `sunburst`, `tile`, and `treemap`.
- `drilldowns` and `dashboard_quality` are optional additive fields for `webapp/` and downstream UI consumers. Consumers must tolerate their absence in older artifacts.

## `queries/content_candidates.json`

Top-level shape:

```json
{
  "version": "1.0",
  "generated_at": "2026-05-10T00:00:00.000000+00:00",
  "source_registry": {"version": "1.0", "sources": []},
  "summary": {
    "total_candidates": 57,
    "by_classification": {
      "dashboard-only hunt": 2,
      "needs field mapping": 48,
      "not applicable to OCI Log Analytics": 7
    }
  },
  "candidates": []
}
```

Candidate records include stable `id`, `title`, `source_url` or `local_reference`, `source_type`, `affected_platform`, MITRE fields, candidate log sources, required fields, detection idea, confidence, licensing/attribution metadata, `review_status`, and a readiness `classification`.

## `queries/log_source_field_dictionary.json`

The field dictionary publishes `fields`, `parsers`, `sources`, `source_candidate_groups`, and validation metadata. Field records include:

- OCI display field name, kind, type, and reserved backing field when applicable
- raw JSON paths and example values
- parser/source ownership
- source candidate groups
- synthetic contract datasets that require the raw path
- saved-search query files that reference the display field

Consumers should use this artifact for schema explorers and field-readiness checks. Reserved parser mappings such as `Original Log Content`/`mbody` are reported under `validation.reserved_mapping_errors`.

## `queries/detection_rule_specs.json`

The detection-rule spec export classifies every query artifact as scheduled-search deployable or not deployable. Each spec includes:

- query file, title, severity, query text, schedule, and lookback
- metric name and up to three dimensions
- ineligibility reasons for dashboard-only or unsupported query shapes
- maturity fields: source confidence, field coverage, test-data coverage, live-validation status, dashboard readiness, and scheduled-rule eligibility
- metadata-only alarm template details; OCI alarms are not created by default

## `queries/catalog.json`

The catalog is the canonical content inventory. UI consumers should use these fields:

- `version`, `generated_at`
- `total_rules`, `total_app_queries`, `total_hunting`, `total_content_items`
- `inventory.source_yaml_rules`
- `inventory.generated_sigma_queries`
- `inventory.total_query_artifacts`
- `platforms`
- `severities`
- `all_mitre_techniques`
- `all_mitre_tactics`
- `stig_controls`
- `rules[]`
- `sentinel_queries[]`
- `app_queries[]`
- `hunting_queries[]`
- `art_coverage`

Catalog rule/query entries use the common display shape:

```json
{
  "title": "OCI Console Login Failure",
  "description": "Detects failed console login attempts...",
  "level": "medium",
  "platform": "oci",
  "mitre_techniques": ["T1078"],
  "mitre_tactics": ["initial_access"],
  "file": "oci_console_login_failure.json"
}
```

Some lists include additional fields such as `sigma_id`, `source_derived`, `stig_ids`, or `stig_category`. Consumers must tolerate missing optional fields.

Microsoft Sentinel converted entries are source-derived and live-gated before dashboard promotion. They appear in `rules[]` and in the Sentinel-specific `sentinel_queries[]` list with this additional shape:

```json
{
  "title": "Failed sign-in burst",
  "description": "Converted from Microsoft Sentinel.",
  "level": "high",
  "platform": "microsoft_sentinel",
  "source_type": "microsoft_sentinel",
  "sentinel_id": "rule-001",
  "sentinel_source_path": "Detections/SigninLogs/failed_signin.yaml",
  "sentinel_source_url": "https://github.com/Azure/Azure-Sentinel/blob/<commit>/...",
  "required_data_connectors": [],
  "conversion_status": "promoted",
  "live_validation_status": "passed",
  "sentinel_category": "identity",
  "sentinel_tables": ["SigninLogs"],
  "mitre_techniques": ["T1078"],
  "mitre_tactics": ["initial_access"],
  "file": "sentinel/failed_signin.json"
}
```

The five Sentinel dashboard groups are loaded from `queries/sentinel/*.json` only when `source_type` is `microsoft_sentinel`, `conversion_status` is `promoted`, and `live_validation_status` is `passed`/`ok`/`success`. Dashboard names are:

- `SOC: Microsoft Sentinel Identity Converted Detections`
- `SOC: Microsoft Sentinel Endpoint Converted Detections`
- `SOC: Microsoft Sentinel Azure Cloud Converted Detections`
- `SOC: Microsoft Sentinel M365 Converted Detections`
- `SOC: Microsoft Sentinel Network Converted Detections`

## `queries/sentinel_conversion_report.json`

The Sentinel report is an operational conversion artifact, not a saved-search query. It records the official Sentinel source metadata, aggregate conversion totals, unsupported feature counts, and one attempted record per ranked candidate.

Current top-level shape:

```json
{
  "version": "1.0",
  "generated_at": "2026-05-13T00:00:00.000000+00:00",
  "source": {
    "name": "Microsoft Sentinel",
    "repository": "https://github.com/Azure/Azure-Sentinel",
    "license": "MIT"
  },
  "summary": {
    "total_candidates": 4452,
    "attempted_candidates": 4452,
    "promoted_count": 421,
    "converted_count": 421,
    "skipped_count": 4031,
    "ranking": "quality-first",
    "live_validation_requested": true,
    "live_validation_passed": 421,
    "live_validation_failed": 53
  },
  "unsupported_features": {},
  "attempted": []
}
```

Attempted records include:

- `sentinel_id`
- `title`
- `quality_score`
- `source_path`
- `source_url`
- `conversion_status`: `promoted`, `converted_not_written`, or `skipped`
- `output_file`: relative `queries/` path when promoted
- `skip_reasons`
- `local_validation_errors`
- `live_validation_status`: `passed`, `failed`, or `not_run`
- `live_validation_error`

Consumers should treat only `conversion_status: promoted` plus `live_validation_status: passed` as runnable saved-search content. Failed live records are retained for triage but are intentionally absent from `queries/sentinel/*.json`.

## `docs/sentinel_converter.html`

The static Sentinel review page is generated from `queries/sentinel_conversion_report.json`, `queries/sentinel/*.json`, and `queries/dashboard_inventory.json`. It is safe to open directly in a browser and includes:

- candidate, attempted, promoted, live-passed, and live-failed counts
- promoted category and severity mix
- Sentinel dashboard widget counts
- top skip reasons
- redacted live-validation failure summaries

The page is a review/reporting surface only. Downstream automation should consume the JSON artifacts, not scrape this HTML.

Use `python3 scripts/sentinel_conversion_workflow.py status --json --strict` for a no-write machine-readable health gate across the report, promoted files, live-validation status, and Sentinel dashboard inventory.
Use `python3 scripts/sentinel_conversion_workflow.py triage --json` for structured blocker analysis without scraping the static HTML page.
Use `python3 scripts/sentinel_conversion_workflow.py next-queries --json` for a prioritized candidate backlog that tells downstream tooling whether the next work is live-validation cleanup, local-validation cleanup, real field mapping, real table/source mapping, or converter feature support.

## `queries/manifest.json`

The manifest is an export payload, not the canonical catalog. Use it when a downstream system needs saved query text or an integration bundle:

- `project`, `version`, `generated_at`
- `stats.total_rules`, `stats.total_sigma_rules`, `stats.platforms`, `stats.severity`
- `rules[]` with `filename`, `title`, `sigma_id`, `level`, `platform`, `service`, `mitre_*`, and `query`
- `dashboards.total`, `dashboards.saved_searches`, `dashboards.names`
- `log_sources`

## `test_data/manifest.json`

The test-data manifest exposes dataset availability without requiring UI code to scan large NDJSON files. `test_data/` is generated locally and ignored by git; regenerate it before ingesting fresh demo data.

```json
{
  "generated_at": "2026-05-06T00:00:00.000000+00:00",
  "total_events": 257922,
  "files": {
    "application_logs.jsonl": {
      "event_count": 1386
    }
  }
}
```

## Deployment Gate

`scripts/deploy_dashboard.py` builds the inventory from `DASHBOARDS`, validates every query reference locally, then validates every unique dashboard query against OCI Log Analytics before importing dashboards by default. Live validation runs each query in an isolated child process so a slow or hung query becomes a validation failure instead of reaching dashboard import. The generated OCI dashboard time parameter and widget default are `l21d`, matching the three-week synthetic dataset; the full demo deploy path also passes `--query-lookback 21d` for deploy-time validation.

Default deployment behavior:

```bash
python3 scripts/deploy_dashboard.py
```

The default path does not import dashboards or embedded saved searches if OCI Log Analytics query validation fails. `--skip-live-validation` is only for local development when OCI access is unavailable.

Tune the validation window or timeout when needed:

```bash
python3 scripts/deploy_dashboard.py --query-lookback 21d --query-timeout 90
```

Static artifact generation:

```bash
python3 scripts/deploy_dashboard.py --export-inventory
```

Use `--export-inventory` for UI development and static schema verification. Use the default deploy command for live OCI dashboard creation.
