# Agent Instructions: oci-log-analytics-detections

## Scope

This repo is scoped to OCI Log Analytics detection content, query generation, synthetic log generation, query/dashboard validation, OCI dashboard creation, and the integrated Forge webapp under `webapp/`.

The integrated `webapp/`, API wrappers, MCP, and cross-platform integrations must consume generated artifacts from here. Do not duplicate query generation or dashboard deployment logic in frontend code.

## Canonical Artifacts

| Artifact | Path | Generator |
|---|---|---|
| Source rules | `rules/**` | hand-authored |
| Sigma-derived queries | `queries/*.json`, `queries/apps/*.json` | `scripts/convert_sigma.py` |
| Sentinel-derived queries | `queries/sentinel/*.json` | `scripts/sentinel_conversion_workflow.py` |
| Curated app analytics | `queries/apps/*.json` | hand-authored |
| Curated hunting analytics | `queries/hunting/*.json` | hand-authored |
| Catalog | `queries/catalog.json`, `CATALOG.md` | `scripts/generate_catalog.py` |
| Dashboard inventory | `queries/dashboard_inventory.json` | `scripts/deploy_dashboard.py` |
| Field/source dictionary | `queries/log_source_field_dictionary.json` | `scripts/field_dictionary.py` |
| Detection rule specs | `queries/detection_rule_specs.json` | `scripts/detection_rule_creator.py` |
| Sentinel conversion report | `queries/sentinel_conversion_report.json` | Sentinel workflow |
| Multicloud export | `queries/manifest.json` | `scripts/export_for_multicloud.py --manifest-only` |
| Forge webapp | `webapp/**` | Next.js app consuming generated artifacts |

## Hard Rules

1. Do not add hand-authored content to `logandetectionqueries/` or `logandetectionrules/`.
2. Do not hand-edit promoted Sentinel JSON under `queries/sentinel/**`; update converter or mapping inputs and promote through live validation.
3. Do not introduce placeholder fields in queries. Every field must map to a real OCI Log Analytics display field or an approved converter built-in.
4. Keep app/APM analytics on `SOC Application Logs` and run `scripts/test_app_query_contract.py` when those queries change.
5. Dashboard placement belongs in `scripts/deploy_dashboard.py`; use visualization metadata and the 12-column layout resolver.
6. README/STATUS counts must reconcile with `queries/catalog.json`.
7. Never commit credentials, API keys, OCIDs, public IPs, tenancy-specific values, or unredacted live error payloads.
8. Keep Forge as the only exposed webapp page; do not expose tenancy data or internal deployment details in UI output.
9. The worktree may contain unrelated user changes. Never revert or commit unrelated changes.

## Common Workflows

Add or update a source detection:

```bash
python3 scripts/convert_sigma.py
python3 scripts/generate_catalog.py
python3 scripts/export_for_multicloud.py --manifest-only
python3 scripts/audit_rule_quality.py --report docs/RULE_QUALITY_REPORT.md
python3 -m pytest -q
```

Update Sentinel conversion coverage:

```bash
python3 scripts/sentinel_conversion_workflow.py local
python3 -m pytest scripts/test_sentinel_converter.py scripts/test_sentinel_conversion_workflow.py -q
python3 scripts/sentinel_conversion_workflow.py status --json --strict
```

Update dashboards or parser contracts:

```bash
python3 -m pytest scripts/test_app_query_contract.py scripts/test_deploy_dashboard.py scripts/test_setup_log_sources.py -q
python3 scripts/deploy_dashboard.py --export-inventory
python3 scripts/deploy_dashboard.py --dry-run
```

Run local release gates:

```bash
python3 scripts/release_checklist.py
```

Live OCI validation requires explicit user direction and a configured profile.

## Project Skill

Use `skills/oci-log-analytics-dashboard-enhancer/` when improving dashboards, choosing visualizations, wiring drilldowns, or pairing dashboards with detection rules.

## Existing Claude Guidance

`CLAUDE.md` contains older project-scoped Claude instructions. Keep this `AGENTS.md` and `CLAUDE.md` aligned when changing repository-level rules.
