# Contributing to OCI Log Analytics Detection Rules

This repository publishes detection content across multiple surfaces. Pick the right surface first, then run the full regeneration and verification loop before opening a pull request.

## Choose the Correct Surface

| If you are adding... | Put it here | Notes |
|----------------------|-------------|-------|
| A source-derived detection rule | `rules/**` | Source of truth is Sigma/YAML |
| A browser-side source-derived detection | `rules/web/browser_attacks/` | These compile into `queries/apps/` |
| Microsoft Sentinel conversion coverage | `config/sentinel_oci_mapping.yaml` + converter tests | Promote only through live validation into `queries/sentinel/` |
| A curated app telemetry analytic | `queries/apps/` | Do not add a `sigma_id` unless the file is source-derived |
| A curated hunting query | `queries/hunting/` | Use OCL analytics operators |

## Source Rule Requirements

- Follow the Sigma rule specification where possible.
- Use descriptive titles and stable UUID-style IDs.
- Include `version`.
- Add MITRE ATT&CK tags such as `attack.initial_access` and `attack.t1190`.
- Add `falsepositives`.
- Add `stig.*` tags when the rule maps to STIG controls.
- Update `config/sigma_oci_mapping.yaml` if the rule needs a new OCI field mapping or log source mapping.

## Contributor Workflow

1. Add or update the rule/query in the correct surface.
2. Regenerate source-derived content and catalogs:

   ```bash
   python3 scripts/convert_sigma.py
   python3 scripts/convert_sigma.py --validate
   python3 scripts/generate_catalog.py
   python3 scripts/export_for_multicloud.py --manifest-only
   python3 scripts/audit_rule_quality.py --report docs/RULE_QUALITY_REPORT.md
   python3 scripts/check_inventory_drift.py
   ```

   If you changed checked-in demo datasets under `test_data/`, regenerate those files so `test_data/manifest.json` stays accurate.

3. Run validation:

   ```bash
   python3 -m unittest discover -s scripts -p 'test_*.py'
   python3 -m compileall scripts
   python3 scripts/deploy_dashboard.py --dry-run
   ```

4. Inspect the generated artifacts you changed:
   - `queries/catalog.json`
   - `queries/manifest.json`
   - affected files under `queries/`, `queries/apps/`, or `queries/hunting/`
5. If the new content should appear on a dashboard, add it to `scripts/deploy_dashboard.py`.

## Microsoft Sentinel Conversion Workflow

Sentinel content is generated from the official `Azure/Azure-Sentinel` corpus. Do not hand-author files under `queries/sentinel/`; update the converter or `config/sentinel_oci_mapping.yaml`, then regenerate.

Rules for Sentinel work:

- `config/sentinel_oci_mapping.yaml` is an allow-list, not a guess table.
- Map only to real OCI Log Analytics sources and fields present in `queries/log_source_field_dictionary.json` or approved converter built-ins.
- Keep failed candidates in `queries/sentinel_conversion_report.json`; do not write them as saved-search query JSON.
- `queries/sentinel/*.json` must have `source_type: microsoft_sentinel`, `conversion_status: promoted`, and `live_validation_status: passed`.
- No alarms or Terraform apply are part of the Sentinel promotion workflow.

Normal Sentinel loop:

```bash
python3 scripts/sentinel_conversion_workflow.py local
python3 -m pytest scripts/test_sentinel_converter.py scripts/test_sentinel_conversion_workflow.py -q
python3 scripts/sentinel_conversion_workflow.py promote --top all --timeout 20
python3 scripts/sentinel_conversion_workflow.py refresh-artifacts
python3 scripts/sentinel_conversion_workflow.py triage
python3 scripts/sentinel_conversion_workflow.py next-queries --work-type field_mapping --limit 10
python3 scripts/sentinel_conversion_workflow.py status --json --strict
```

Use `python3 scripts/sentinel_conversion_workflow.py status --json` for reporting and add `--strict` when CI should fail on mismatched reports, promoted files, live status, or missing Sentinel dashboards.
Use `python3 scripts/sentinel_conversion_workflow.py triage --json` when automation needs the top skip reasons, local validation errors, live-failure examples, and suggested next actions.
Use `python3 scripts/sentinel_conversion_workflow.py next-queries --json` to pick specific candidates for the next mapping or converter iteration without hand-authoring files under `queries/sentinel/`.

## Validation Expectations

Before submitting a PR:

- Rule quality audit should report 0 issues.
- Unit tests should pass.
- Dashboard dry-run should resolve dashboard/query references cleanly.
- Generated inventory should match the current repo contents.
- If you touched `test_data/*.jsonl`, `test_data/manifest.json` should reflect the new file counts and event totals.

## Live OCI Validation

When you have access to the target OCI tenancy, run the live validation path as well:

```bash
python3 scripts/setup_log_sources.py
python3 scripts/setup_streaming_pipeline.py
python3 scripts/validate_pipeline.py --e2e
python3 scripts/verify_caldera_detections.py --operation discovery --lookback 60d
```

Notes:

- `SOC Application Logs` is the supported browser/app telemetry surface for the dashboards under `queries/apps/`.
- `setup_streaming_pipeline.py` and `validate_pipeline.py` now use `config/streaming_config.json` as the runtime contract for expected SOC streams/connectors, including multicloud-health when it is configured.

## Field Mapping

If a rule uses a field not yet mapped to OCI Log Analytics:

1. Open `config/sigma_oci_mapping.yaml`.
2. Add the field under `field_mappings` or the log source under `logsource_mappings`.
3. Re-run `python3 scripts/convert_sigma.py` and inspect the generated query.

## Review Notes

- `queries/catalog.json` is the canonical inventory.
- `queries/manifest.json` is an export artifact, not the canonical inventory.
- `logandetectionqueries/` and `logandetectionrules/` are legacy empty directories and should not be used by new tooling.
