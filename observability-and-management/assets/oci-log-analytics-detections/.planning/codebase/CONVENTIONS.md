---
last_mapped_commit: 671c18eb3203a99666d170682997de48cb43f0f2
mapped_at: 2026-05-14
focus: quality
---

# Conventions

## Content Boundaries

- Add source-derived detections under `rules/**`, then regenerate queries.
- Add curated app analytics under `queries/apps/**`.
- Add curated hunting analytics under `queries/hunting/**`.
- Do not add new content under `logandetectionqueries/` or `logandetectionrules/`.
- Do not hand-edit promoted Sentinel query JSON; change converter/mapping inputs instead.

## Python Style

- Scripts are plain Python modules in `scripts/`.
- Tests import scripts directly by adding `scripts/` to `sys.path` where needed.
- Prefer deterministic generation with stable sort/order because generated JSON and docs are reviewed in git.
- Existing code often favors module-level constants for dashboard/query/parser definitions.
- Keep validation failures explicit. Avoid broad `pass` or swallowed exceptions in new code.

## Query and Field Conventions

- Use OCI Log Analytics display field names that exist in parser/source dictionaries.
- Quote string-typed fields such as Windows `'Event ID' = '4688'`.
- Avoid unsupported live-validation query patterns blocked by dashboard tests.
- For multi-word phrase `LIKE` matching in OCI LA, prefer wildcard-token form such as `*token1*token2*`.
- `SOC Application Logs` is the correct source for app/browser/APM dashboard queries.

## Dashboard Conventions

- Edit dashboard definitions in `scripts/deploy_dashboard.py`.
- Use visualization metadata for width/height; let `resolve_widget_layout()` compute placement.
- Export and review `queries/dashboard_inventory.json` after dashboard changes.
- Keep dashboard query files and widget references in sync.

## Documentation Conventions

- README/STATUS inventory counts should reconcile with generated artifacts.
- `queries/catalog.json` is authoritative for counts.
- Add or update docs when a project-level contract changes.
- Use placeholders for profiles, regions, compartments, OCIDs, and IP addresses in committed docs.

## GSD Conventions

- Use `.planning/PROJECT.md` and `.planning/STATE.md` as the current context source.
- Use `$gsd-plan-phase <n>` before substantial implementation work.
- Use `$gsd-audit-fix` for concrete review/test/audit findings.
- Update `.planning/STATE.md` after phase completion or major handoffs.
- Do not auto-commit from GSD workflows while unrelated user changes are present.
