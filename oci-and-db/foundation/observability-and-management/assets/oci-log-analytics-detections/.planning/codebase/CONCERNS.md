---
last_mapped_commit: 671c18eb3203a99666d170682997de48cb43f0f2
mapped_at: 2026-05-14
focus: concerns
---

# Concerns

## Dirty Worktree

The repo currently has a broad dirty worktree with many modified, deleted, and untracked files. Future GSD workflows must:

- Check `git status --short` before editing.
- Isolate changes to the task scope.
- Avoid `git checkout --`, `git reset`, or generated artifact cleanup unless explicitly requested.
- Avoid committing if the target file already contains unrelated user edits that cannot be staged separately.

## Generated Artifact Drift

Many docs and JSON files are generated or count-bearing. Any change to rules, queries, dashboards, parser mappings, Sentinel reports, or synthetic data can require multiple regenerated artifacts.

Risk surfaces:

- README/STATUS count drift from `queries/catalog.json`.
- Dashboard inventory drift from `scripts/deploy_dashboard.py`.
- Field dictionary drift from parser mappings or synthetic contracts.
- Sentinel conversion report mismatch with promoted files.

## Live OCI Coupling

Some workflows need live OCI parser or dashboard validation. These are high-value but environment-dependent:

- Active `OCI_PROFILE` may differ by operator.
- Namespace, compartment, and source readiness can differ by tenancy.
- Live validation should be explicit, not automatic.

## Sentinel Backlog Scale

`queries/sentinel_conversion_report.json` currently records 4,452 attempted candidates, 421 promoted live-passed queries, 53 live failures, and many skipped candidates. Improvements must be bucketed and tested incrementally.

## Parser Field Fragility

Dashboard queries depend on display fields extracted by custom parsers. Adding fields to queries without updating:

- `scripts/setup_log_sources.py`
- `queries/log_source_field_dictionary.json`
- `config/synthetic_log_contracts.json`
- app/query contract tests

can produce dashboards that dry-run locally but fail live.

## Secret and Tenant Hygiene

This repo includes deployment and live validation tooling. Guard against committing:

- OCIDs
- public IPs
- tenancy names
- profile-specific compartment values
- API keys or auth tokens
- unredacted live error payloads

## Legacy Directories

`logandetectionqueries/` and `logandetectionrules/` remain present but should not receive new content. New tools must consume `queries/**` and generated inventory artifacts instead.
