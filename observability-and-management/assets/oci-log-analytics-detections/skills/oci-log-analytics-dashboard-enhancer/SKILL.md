---
name: oci-log-analytics-dashboard-enhancer
description: Use when enhancing Oracle Cloud Infrastructure Log Analytics dashboards, saved searches, visualizations, widget layouts, tile-in-link layouts, drilldowns, app/APM log queries, or detection-rule-backed alerting. Apply this skill whenever dashboards have overlapping widgets, query fields need source/parser validation, saved-search visualization metadata is changing, or detection rules and dashboard widgets need to be correlated. Also use when extending the Microsoft Sentinel KQL → Logan QL converter — operator extractions, canonicalizer or tier-classifier changes, mapping-allow-list edits, or designing a similar source-language converter (Splunk SPL, Elastic ES|QL) on top of the same `scripts/kql/` + OPERATOR_REGISTRY scaffolding.
---

# OCI Log Analytics Dashboard Enhancer

Use this skill when the task is to improve an OCI Log Analytics dashboard or saved search, add a new visualization, make a widget more actionable, or pair a dashboard view with a detection rule and alarm path.

## First decisions

Start by identifying the correct surface:

- Source-derived detection rule: `rules/**`
- Generated OCI query derived from Sigma: run `scripts/convert_sigma.py`
- Source-derived Microsoft Sentinel rule or hunting query: use the Sentinel workflow wrapper in `scripts/sentinel_conversion_workflow.py`; it delegates to `scripts/convert_sentinel_kql.py`
- Curated app telemetry analytic: `queries/apps/*.json`
- Curated hunting or dashboard analytic: `queries/hunting/*.json`
- Dashboard composition and widget wiring: `scripts/deploy_dashboard.py`

Then decide whether the ask is primarily:

- A KPI or summary view
- An investigative drilldown
- A relationship or anomaly view
- A geographic view
- A detection and alerting workflow

## Repo-specific rules

Read [repo-integration.md](references/repo-integration.md) before editing dashboards in this repository.

Key local constraints:

- Dashboard widgets are embedded saved searches created by `scripts/deploy_dashboard.py`.
- Query JSON can define dashboard metadata under `dashboard.visualizationType`, `dashboard.visualizationOptions`, `dashboard.timeSelection`, `dashboard.layout`, and `dashboard.ask_ai_prompts`.
- Widget entries in `DASHBOARDS` can override query metadata with `visualization_type`, `visualization_options`, `time_selection`, `layout`, and `ask_ai_prompts`.
- Dashboard placement uses a 12-column grid. `resolve_widget_layout()` merges visualization defaults, query layout, and widget layout; `build_dashboard_json()` assigns `row` and `column` and wraps widgets when a row is full.
- Avoid hand-authored `row` or `column` metadata unless you are deliberately extending the placement algorithm. Most dashboard changes should only set `width` and `height`.
- App and APM analytics must stay on the supported `SOC Application Logs` schema and pass `scripts/test_app_query_contract.py`.
- Sentinel conversions must stay on the real OCI field/source allow-list in `config/sentinel_oci_mapping.yaml` and `queries/log_source_field_dictionary.json`; do not add placeholder or guessed fields just to increase conversion count.
- Keep new analytics in the right surface; do not add hand-authored content under `logandetectionqueries/` or `logandetectionrules/`.

## Dashboard layout guardrails

Use the repo layout helpers instead of inventing per-dashboard placement.

- Start with the visualization defaults in `VISUALIZATION_LAYOUT_DEFAULTS`.
- Prefer full-width `12x5` or `12x6` tiles for `table`, `summary_table`, `records`, `records_histogram`, `table_histogram`, `link`, `cluster`, `issues`, and `map` widgets because these usually expose wide investigation fields.
- Use compact `3x3` tiles only for KPI-style `tile` or `distinct` widgets.
- Use `6x5` or `6x6` for compact charts such as `line`, `bar`, `hbar`, `pie`, `sunburst`, and `treemap`.
- Keep `width` between `1` and `12`; keep `height` positive.
- Before considering a dashboard complete, build the dashboard JSON and verify tile rectangles do not overlap. The focused unit test is `test_build_dashboard_json_layout_prevents_tile_overlap`.

## Visualization selection

Read [oracle-log-analytics-capabilities.md](references/oracle-log-analytics-capabilities.md) when you need command limits, URL parameters, tile XML, or detection-rule guardrails.

Use these defaults:

- `summary_table`: best default for KPI rollups and multi-field correlation.
- `tile`: single KPI, distinct count, or period-over-period metric.
- `records` or `table`: when analysts need raw rows.
- `records_histogram` or `table_histogram`: when fast drilldown from time buckets matters.
- `sunburst` or `treemap`: hierarchical composition across 2-3 grouping fields.
- `link`: transaction or relationship analysis across fields and time.
- `cluster` or `issues`: high-volume anomaly triage, not routine scorecards.
- `map`: spatial analysis. In this repo, inspect the existing geographic-health queries before changing shape.
- `tile` in `link`: compact executive summaries or hidden detail panes behind a single widget.

Default to the simplest visualization that answers the operator question. Do not force exotic charts onto routine SOC dashboards.

## Visualization render-safety (CRITICAL — learned 2026-06-09)

OCI's dashboard renderer adds a hidden records-companion query for some widget
types: it appends `| fields Time` (chart/grid companion) or `| fields ID` (table
row identity) to the saved-search query at **render time**. After an aggregation
those fields do not exist, so the widget shows a banner error:

- `timestats … | fields ID`  → **"Invalid field for FIELDS after TIMESTATS: ID"**
- `stats … | fields Time`     → **"Invalid field for FIELDS after STATS: Time"**

This is invisible to `scripts/parse_validate_all_queries.py` (uses `parse_query`,
syntax only) **and** to a direct `LogAnalyticsClient.query()` — both pass. It only
reproduces in the live dashboard, or by manually appending `| fields ID` /
`| fields Time` to the query via the query API. So a green parse gate and green
deploy-time live validation are **not** sufficient; the visualization/query
pairing must also be render-safe.

Safe pairings (enforce these):

| Query shape | Use | Never use |
|---|---|---|
| `timestats … by X` (timeline) | `line` + `visualizationOptions {timeField:"Time", seriesField:X, valueField:<metric>}` and an explicit `span` | `table`, `records`, `sunburst`, `bar` (timestats→table appends `ID`) |
| `stats … by X` (rollup) | `summary_table` (or plain `table` — safe for stats) | `sunburst`, `line`, `pie`, `treemap` (stats→chart appends `Time`) |
| `stats … by A,B` hierarchy | `summary_table` | `sunburst`/`treemap` (they append `Time` and error) |
| single value | `tile` + `dataField` | — |
| `link … | eventstats` | `link` (+ `tileLayoutXml`) | — |

Rules of thumb:

- A `line`/timeline widget MUST carry `timeField` (or `xField`) **and**
  `valueField` in `visualizationOptions`; without them OCI cannot map the
  timestats output to axes and falls back to a records render that errors.
- Plain `table` is safe for `stats` output (it shows the stat columns) but NOT
  for `timestats` output (OCI adds a row `ID`).
- Sunburst is attractive but currently triggers the `stats→Time` append — prefer
  `summary_table` for MITRE/OWASP rollups on this platform until proven otherwise.
- `bar`/`hbar` (categorical x-axis) do not append a time grid and are safe for
  `stats`.

The Sentinel generator encodes this: `scripts/convert_sentinel_kql.py`
`_dashboard_metadata()` maps any `stats`/`timestats`/`eventstats` query to
`summary_table`, never `table`.

## Deploy gotcha: --cleanup soft-delete resurrection (learned 2026-06-09)

`scripts/deploy_dashboard.py --cleanup` soft-deletes saved searches. OCI keeps a
soft-deleted saved search by ID for a window; re-importing a saved search with the
**same stable ID** within that window **resurrects the old saved search** (stale
`visualizationType` / `timeSelection`) instead of applying the new `uiConfig`. The
symptom: deploys report success but the live dashboard keeps the old widget count
and old time window (e.g. stays at `l24h` after you changed everything to `l21d`).

Fix (now in `build_dashboard_json`): embedded saved-search IDs carry the
dashboard's per-deploy timestamp suffix (`<query-file>-<ts>`), the same way
dashboard IDs already do, so every deploy mints fresh IDs and cannot collide with
a soft-deleted one. The tile's `savedSearchId` uses the same suffixed ID. Regression
test: `test_build_dashboard_json_saved_search_ids_unique_per_deploy`.

When a live dashboard looks stale, verify what is actually deployed (do not trust
the deploy summary): fetch the dashboard via `DashxApisClient.get_management_dashboard`
and inspect each `saved_searches[].ui_config` `visualizationType`/`timeSelection`.

## Time window for demo data

`DEFAULT_DASHBOARD_TIME_PERIOD` is `l21d` so dashboards open on the full 3-week
synthetic window (a `l24h` default shows ~1/21 of the spread data and most sparse
detections render empty). The dashboard time parameter default and all
non-overridden widgets inherit it.

## Compartment scope gotcha

Dashboards and data both live in the deploy `COMPARTMENT_ID`. If the OCI Console
resource-scope filter (`rs=` in the URL / the scope picker) points at a different
compartment, every widget shows "no data" even though the data exists. Confirm the
console scope matches the deploy compartment (and Include sub-compartments = on)
before assuming a data or query problem.

## Query design heuristics

For dashboard-friendly analytics:

- Prefer `stats` for summary widgets and tables.
- Prefer `timestats` for trends and service-health timelines.
- Use `link` when the analysis is about grouped transactions, sessions, entities, or multi-step activity.
- Use `compare` only for interactive link/time comparisons, not for scheduled-search detection rules.
- Use `geostats` only when the target view really needs map semantics; scheduled-search detection rules do not support it.

For widget output:

- Keep field names readable and stable.
- Alias the metric field intentionally.
- Limit cardinality before putting the result on a dashboard.
- Keep `stats by` groupings to four fields or fewer for app/dashboard queries.
- If the chart is noisy, sort or reduce to top/bottom values before rendering.

## App/APM query contracts

For Octo APM Demo and other application observability dashboards:

- Use `'Log Source' = 'SOC Application Logs'` and the parser/source field names defined by the synthetic log contract.
- Correlate logs, spans, and metrics with quoted dashboard fields such as `'Trace ID'`, `'Span ID'`, `'Span Name'`, `'Service Name'`, `'APM Domain'`, `'Workflow ID'`, `'Workflow Step'`, `'Run ID'`, and `'Metric Name'`.
- For threat-hunting workshop stories, preserve fields that let users pivot across evidence: `'Attack ID'`, `'Attack Stage'`, `'MITRE Technique ID'`, `'Payment Redirect URL'`, `'Compromised VM'`, `'Host Name'`, and `'OSQuery Finding'`.
- Avoid legacy application tokens blocked by `scripts/test_app_query_contract.py`, including unquoted OTel-style names such as `service.name`, `trace_id`, `http.status_code`, and `http.response_time_ms`.
- Pair correlation widgets deliberately: one trend/timeline, one trace/span rollup, one error or payment-threat table, and one raw-log or link view for investigation.
- Do not put LAQL colon placeholders such as `:attack_id`, `:trace_id`, or `:request_id` in saved-search or dashboard queries. OCI Log Analytics rejects them in dashboard widgets with parser errors like `Unexpected input for WHERE: :attack_id` or `Unexpected input for SEARCH: :attack_id`. Dashboard-safe queries must run without runtime placeholders; for manual pivots, document copied Log Explorer filters with placeholder literals such as `'Attack ID' = '<ATTACK_ID>'`.

Current Octo APM workshop baseline, last live-verified in `emdemo` on 2026-05-12:

- `OCI-DEMO: Octo APM Demo Dashboard` has 17 tiles and 17 embedded saved searches pinned to `l21d`.
- The dashboard returned 17/17 widget HITs over `24h` after fresh workshop evidence ingestion.
- The Octo APM detection-rule query pack returned 5/5 HITs over `24h`.
- Five scheduled-search rules were present and `ACTIVE`/`READY` with `MONITORING` as the target service.
- Keep all docs, examples, and runbooks variable-safe. Use placeholders such as `${OCI_PROFILE}`, `${OCI_COMPARTMENT_ID}`, `${LA_NAMESPACE}`, `${LOG_ANALYTICS_LOG_GROUP_ID}`, `<ATTACK_ID>`, and `<TRACE_ID>` instead of tenancy values, OCIDs, hostnames, or IP addresses.

## Microsoft Sentinel conversion workflow

Use this path when promoting official Microsoft Sentinel KQL into OCI Log Analytics / Logan QL.

Read [kql-conversion-architecture.md](references/kql-conversion-architecture.md) before adding a new operator, mapping a new KQL function, splitting the converter into smaller modules, or designing a different source-language converter (Splunk SPL, Elastic ES|QL, etc.). That file documents the `scripts/kql/` subpackage layout, the `OPERATOR_REGISTRY` dispatch pattern, the `canonical()` form used for snapshot testing, the `Tier` classifier, the behavior-preserving refactor strategy that produced Phase 6, and the entry-point compatibility rules.

Canonical surfaces:

- Source cache: `.sentinel/Azure-Sentinel/` is local cache only and must not be committed.
- Candidate export: `queries/sentinel_candidates.json` is generated intake data and must not be committed unless the project policy changes.
- Mapping allow-list: `config/sentinel_oci_mapping.yaml`.
- Converter facade: `scripts/convert_sentinel_kql.py` (≤800 lines — CLI + I/O orchestration + re-exports for the D-15 public surface).
- Converter implementation: `scripts/kql/` subpackage (`types.py`, `canonical.py`, `lexer.py`, `pipeline.py`, `operators/<op>_op.py`, `_facade_impl.py` Phase 7+ staging area).
- Operator dispatch: `scripts.kql.operators.OPERATOR_REGISTRY` (Phase 6: 12 supported families + 9 unsupported, all registered via `@register("<op>")`).
- Test harness: `scripts/test_kql/` (Hypothesis idempotence, 18 golden fixtures, line-budget gate, operator-level unit tests).
- Simple operator workflow: `scripts/sentinel_conversion_workflow.py`.
- Promoted query surface: `queries/sentinel/*.json`.
- Conversion report: `queries/sentinel_conversion_report.json` (Phase 6: includes `summary.tier_distribution` and per-candidate `tier`).
- Static review page: `docs/sentinel_converter.html`.

Subpackage decision rules (more in [kql-conversion-architecture.md](references/kql-conversion-architecture.md)):

| Change shape | Goes in |
|---|---|
| New per-operator rewrite | `scripts/kql/operators/<op>_op.py` (function returns `StageResult`) |
| New KQL function rewrite | `scripts/kql/functions/<fn>.py` |
| Stage splitting / tokenizing | `scripts/kql/lexer.py` (or `_facade_impl.py` during Phase 7 redistribution) |
| Field/table mapping rule | `config/sentinel_oci_mapping.yaml` (data, not code) |
| Logan QL output validator | `validate_logan_query_local` (Phase 6 lives in `scripts/kql/_facade_impl.py`; Phase 7 lifts it into a dedicated validator module) |
| Ranking / payload / CLI / report | `scripts/convert_sentinel_kql.py` (the facade) |
| Operator commands (`local`, `promote`, …) | `scripts/sentinel_conversion_workflow.py` |

Default promotion policy:

- Ingest only official `Azure/Azure-Sentinel` content.
- Rank quality-first, but promote only candidates that pass both local validation and live OCI Log Analytics parser validation.
- Keep nonworking candidates in `queries/sentinel_conversion_report.json` with skip or live-failure reasons.
- Do not create alarms or run Terraform from the Sentinel converter flow.
- Dashboard groups should reference only `queries/sentinel/*.json` files with `live_validation_status: passed`.

Field and source mapping rules:

- Treat `config/sentinel_oci_mapping.yaml` as an allow-list, not a guess table.
- A mapped Logan field must exist in `queries/log_source_field_dictionary.json`, the converter's built-ins, or the approved Azure audit schema fields.
- Prefer dropping Sentinel entity-enrichment aliases such as `AccountCustomEntity`, `HostCustomEntity`, `IPCustomEntity`, `URLCustomEntity`, `DNSCustomEntity`, and `MalwareCustomEntity`; they describe Microsoft entity binding, not Logan fields.
- Preserve original Sentinel metadata on every promoted JSON: `source_type: microsoft_sentinel`, `sentinel_id`, `sentinel_source_path`, source URL, attribution/license, required connectors, MITRE metadata when present, severity, table names, and conversion status.
- Never promote queries with unresolved placeholders such as `{{...}}`, `GOES HERE`, `REPLACE_ME`, or colon parameters.
- Strip KQL explicit time filters such as `TimeGenerated > ago(...)`; OCI dashboard and validation windows provide the time range.
- Unsupported or unsafe KQL remains skipped: tabular `let`, `join`, `make-series`, `mv-expand`, `datatable`, watchlists, `externaldata`, custom functions, regex extraction/predicate, complex JSON bag expansion, `strlen`, `toint`, and raw `int(...)`.

Simple commands:

```bash
# Fast local conversion report without overwriting the canonical live report.
python3 scripts/sentinel_conversion_workflow.py local

# Live-validate and write only working Sentinel queries.
python3 scripts/sentinel_conversion_workflow.py promote --top all --timeout 20

# Regenerate catalog, dashboard inventory, dashboard validation, and the HTML status page.
python3 scripts/sentinel_conversion_workflow.py refresh-artifacts

# Full promotion loop: live promotion, catalog/inventory refresh, validation, HTML page.
python3 scripts/sentinel_conversion_workflow.py all --top all --timeout 20

# Rebuild only the static web review page from the latest report.
python3 scripts/sentinel_conversion_workflow.py page

# Summarize conversion blockers without rerunning conversion.
python3 scripts/sentinel_conversion_workflow.py triage
python3 scripts/sentinel_conversion_workflow.py triage --json

# Pick concrete Sentinel candidates for the next development iteration.
python3 scripts/sentinel_conversion_workflow.py next-queries --limit 10
python3 scripts/sentinel_conversion_workflow.py next-queries --work-type field_mapping --json

# Check report/file/dashboard consistency without rerunning conversion.
python3 scripts/sentinel_conversion_workflow.py status
python3 scripts/sentinel_conversion_workflow.py status --json
python3 scripts/sentinel_conversion_workflow.py status --json --strict
```

Developing later/new Sentinel queries:

1. Use `triage` to understand the dominant blocker classes.
2. Use `next-queries` to select a small, quality-aware candidate queue.
3. For `field_mapping` and `table_mapping`, verify real OCI parser/source support before editing `config/sentinel_oci_mapping.yaml`.
4. For `live_environment`, rerun after OCI auth/clock-skew issues are healthy before changing converter logic.
5. For `local_validation`, `live_validation`, and `kql_support`, change the deterministic converter and add focused tests; do not patch generated Sentinel JSON by hand.
6. Run `local`, then live-gated `promote`, then `refresh-artifacts`, `page`, `status --json --strict`, focused tests, and compile/full tests as appropriate.

Latest Sentinel baseline from the current repo state:

- 4,452 official Sentinel candidates attempted.
- 474 locally clean conversions after strict field/token validation.
- 421 live OCI parser-passing queries promoted under `queries/sentinel/`.
- 53 live validation failures retained in the report and not written as saved searches.
- Promoted category split: endpoint 252, M365 72, network 59, identity 27, Azure/cloud 11.
- Sentinel dashboards are generated in five groups capped at 24 widgets each: Identity, Endpoint, Azure Cloud, M365, and Network.

Phase 6 converter-architecture baseline (recorded 2026-05-16):

- `scripts/convert_sentinel_kql.py` is **678 lines** (under the 800-line CLAUDE.md hard rule). The `__all__` list pins the D-15 public surface.
- `scripts/kql/_facade_impl.py` holds the relocated converter helpers (1227 lines) — Phase 7+ will redistribute them into the operator modules, the lexer, and a dedicated validator module.
- The Phase 6 legacy adapter file (in `scripts/kql/operators/`) was deleted in plan 06-10; the residual unsupported set lives in `scripts/kql/operators/unsupported_op.py` as real Tier-3 functions.
- `OPERATOR_REGISTRY` lists 21 entries: 12 supported families dispatched through extracted modules (`where`, `summarize`, `project`/`fields`/`project-reorder`, `extend`, `sort`/`order`, `top`, `distinct`, `union`, `let`) + 9 unsupported (`take`, `count`, `limit`, `parse`, `evaluate`, `mv-expand`, `make-series`, `join`, `render`).
- `queries/sentinel_conversion_report.json` carries `summary.tier_distribution` (currently `{tier_1: 8, tier_2: 0, tier_3: 17}`) and a `tier` field on every `attempted[]` entry.
- `scripts/test_kql/` holds 88 passing tests covering canonicalizer idempotence (Hypothesis, 100 examples), 18 golden fixtures (8 promoted + 10 synthetic), the line-budget gate, and operator-level unit tests (registry binding regression-fence + Tier-1 / Tier-3 paths per operator).
- `requirements-dev.txt` contains exactly two lines: `pytest>=8.3` and `hypothesis>=6.150`.
- Deferred to Phase 7: rewire `scripts/kql/pipeline.convert` to dispatch through `OPERATOR_REGISTRY` instead of delegating to legacy `convert_kql_to_logan`. Operator modules ARE registered and tested; only the pipeline wiring sits behind the legacy delegation.

## Drilldowns and navigation

When the user wants dashboards to feel more actionable:

- Prefer Log Explorer deep links over static prose.
- Use copied query URLs or encoded queries so the destination opens with the right query, filters, visualization, time range, and scope.
- For tile-in-link XML, store the XML in `dashboard.visualizationOptions.tileLayoutXml` and set `dashboard.visualizationOptions.dashboardOptions` to include `Tiles` and `Main Table`.
- For link widgets with custom tiles, add summary fields to the link query with `eventstats` so every `<tile field="...">` has a matching output field.
- Use hidden tiles plus `show(id=...)` or expander patterns for layered drilldown when one link widget needs multiple detail panes.
- Keep deep links aligned with the dashboard time range and scope filters.

## Detection-rule path

Choose one mechanism:

- Ingest-time detection rule: for label-based matching in a known log source or entity type, where every matching record should emit a metric immediately.
- Scheduled-search detection rule: for LAQL logic that must run periodically and post a numeric metric plus optional dimensions.
- Template-based detection rule: when an Oracle-defined template already models the use case.

For scheduled-search detection rules:

- The query must produce a valid numeric metric.
- You can post up to three dimensions.
- If using `link` output as dimensions, end the query with `fields -*, dim1, dim2, dim3, metric1`.
- Account for late-arriving logs if the detection window is short.
- Avoid unsupported commands and expensive patterns listed in the reference file.

For ingest-time detection rules:

- The rule depends on labels defined in the source/parser layer.
- Validate that the label, log source, and entity filter are specific enough to avoid noisy metrics.

Detection rules are not alarms. The rule posts metrics to Monitoring; the alarm is configured separately on that metric.

## Working pattern in this repo

1. Inspect the target query JSON and the dashboard entry in `scripts/deploy_dashboard.py`.
2. Decide whether the dashboard improvement needs only query changes, only widget wiring, or both.
3. Put visualization metadata in the query `dashboard` block unless the same query needs different behavior in different dashboards; use widget-level overrides only for those per-dashboard differences.
4. If the ask includes alerting, shape the query so it also works as a scheduled-search detection rule, or add the required label path for ingest-time rules.
5. Keep titles, descriptions, tags, and log-source metadata consistent with nearby content.
6. Regenerate derived artifacts only when the touched surface requires it.

## Validation

After edits, run the smallest relevant validation loop:

- `python3 scripts/deploy_dashboard.py --dry-run` for all dashboard wiring
- `python3 scripts/deploy_dashboard.py --dry-run --dashboard-name "<target dashboard>"` for focused dashboard checks
- `python3 scripts/deploy_dashboard.py --validate` for dashboard inventory validation
- `python3 -m unittest scripts.test_deploy_dashboard scripts.test_app_query_contract -q`
- `python3 -m unittest discover -s scripts -p 'test_*.py'`
- `python3 -m compileall scripts`

If you changed source-derived rules or catalogs, also run:

- `python3 scripts/convert_sigma.py`
- `python3 scripts/generate_catalog.py`
- `python3 scripts/export_for_multicloud.py --manifest-only`

If you changed Sentinel conversion code, mapping, or promoted queries, run the Sentinel-specific loop:

- `python3 -m pytest scripts/test_sentinel_converter.py scripts/test_sentinel_conversion_workflow.py -q`
- `python3 scripts/sentinel_conversion_workflow.py local`
- `python3 scripts/sentinel_conversion_workflow.py page`
- `python3 scripts/generate_catalog.py`
- `python3 scripts/deploy_dashboard.py --export-inventory`
- `python3 scripts/deploy_dashboard.py --validate`
- Focused dry-runs for every nonempty `SOC: Microsoft Sentinel * Converted Detections` dashboard.
- `python3 -m compileall scripts`

## Output expectations

When using this skill, produce:

- The recommended visualization choice and why it fits the analyst task
- The exact repo surface to edit
- Any query-shape changes needed for charting or metrics
- Any dashboard deployment changes needed to persist the visualization
- Any detection-rule and alarm follow-up needed for alerting
