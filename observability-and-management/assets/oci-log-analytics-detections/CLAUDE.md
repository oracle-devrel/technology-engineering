# CLAUDE.md — oci-log-analytics-detections

Project-scoped operating rules for Claude Code in this repository.

## Scope

This repo is **scoped to OCI Log Analytics**: query generation from Sigma/Sentinel sources, synthetic log generation, query/dashboard validation, OCI dashboard creation, and the integrated Forge webapp under `webapp/`. UI/API/cross-platform code **must consume artifacts from here** and must not duplicate query generation or dashboard deployment.

## Canonical artifacts (do not duplicate)

| Artifact | Path | Generator |
|---|---|---|
| Source rules | `rules/**` | hand-authored |
| Sigma-derived queries | `queries/*.json`, `queries/apps/*.json` | `scripts/convert_sigma.py` |
| Sentinel-derived queries | `queries/sentinel/*.json` | `scripts/sentinel_conversion_workflow.py` |
| Curated app analytics | `queries/apps/*.json` (38 curated) | hand-authored |
| Hunting analytics | `queries/hunting/*.json` (87) | hand-authored |
| Catalog | `queries/catalog.json`, `CATALOG.md` | `scripts/generate_catalog.py` |
| Dashboard inventory | `queries/dashboard_inventory.json` | `scripts/deploy_dashboard.py` |
| Field/source dictionary | `queries/log_source_field_dictionary.json` | `scripts/field_dictionary.py` |
| Detection rule specs | `queries/detection_rule_specs.json` | `scripts/detection_rule_creator.py` |
| Sentinel conversion report | `queries/sentinel_conversion_report.json` | Sentinel workflow |
| Multicloud export | `queries/manifest.json` | `scripts/export_for_multicloud.py --manifest-only` |
| Forge webapp | `webapp/**` | Next.js app consuming generated artifacts |

## Hard rules

1. **No hand-authored content** in `logandetectionqueries/` or `logandetectionrules/` — generated only.
2. **No placeholder fields.** Every Sigma/Sentinel field must exist in `config/sentinel_oci_mapping.yaml` or `queries/log_source_field_dictionary.json`.
3. **Sentinel conversions promote only after live OCI parser validation** (10 known live failures are retained in the report and NOT promoted).
4. **Dashboard placement uses the 12-column algorithm** in `scripts/deploy_dashboard.py:resolve_widget_layout()`. Set `width`/`height` only — do not hand-author `row`/`column`.
5. **App/APM analytics stay on `SOC Application Logs`** and must pass `scripts/test_app_query_contract.py`.
6. **README/STATUS counts must reconcile with `queries/catalog.json`** before commit.
7. **No public IPs, OCIDs, credentials, or tenancy specifics** in committed files (global rule — see `~/.claude/CLAUDE.md`).
8. **Forge-only exposure**: keep `/forge`, `/api/forge/*`, `/api/health`, and required static assets as the exposed webapp surface.

## Workflow

1. **Add detection** → author in `rules/**` → run `scripts/convert_sigma.py` → confirm `queries/catalog.json` updates → add synthetic events under `test_data/` if needed.
2. **Add Sentinel rule** → run `scripts/sentinel_conversion_workflow.py local` → review `sentinel_conversion_report.json` → only promote with `promote` after live validation passes.
3. **Add/edit dashboard** → edit `DASHBOARDS` in `scripts/deploy_dashboard.py` → run live-query validation → `scripts/release_checklist.py` before promoting to a live profile.
4. **Counts changed** → run `scripts/generate_catalog.py` → update README/STATUS to match.

## Agents (`.claude/agents/`)

- **explorer** — read-only path tracing across rules→queries→dashboards
- **docs-researcher** — verify claims against repo references + primary OCI/Sigma/Sentinel docs
- **reviewer** — owner-grade review for detection/dashboard/script changes

Use `code-reviewer` and `security-reviewer` (global) for cross-cutting passes; use the project agents above for repo-specific invariants.

## Skill

`skills/oci-log-analytics-dashboard-enhancer/` — invoke whenever the task is to improve a dashboard, choose a visualization, wire a drilldown, or pair a dashboard with a detection rule. See `SKILL.md` for first-decision flow and layout guardrails.

## Release gates

- `scripts/release_checklist.py` — local gates + optional live profile verification (`--include-live`)
- `scripts/parse_validate_all_queries.py` — fast live `parse_query` gate over every `queries/**` query (syntax + field/source validity, no data needed); runs under `--include-live` and writes `docs/health/parse-validate-all.json`. Use this to isolate broken queries (ERROR) from no-data (the execution smoke test's MISS). `eval`/`if` accept only equality/comparison — no `case`, `decode`, `coalesce`, or `like` inside `eval`.
- `docs/health/all-dashboard-verify.json` — latest live dashboard health
- Live baseline: `<OCI_PROFILE_CAP>` shows 351/351 dashboard widgets HIT, 0 MISS, 0 ERROR; `parse_validate_all_queries.py` shows 678/678 queries PASS
