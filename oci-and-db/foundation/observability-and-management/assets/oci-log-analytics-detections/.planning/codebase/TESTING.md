---
last_mapped_commit: 671c18eb3203a99666d170682997de48cb43f0f2
mapped_at: 2026-05-14
focus: quality
---

# Testing

## Framework

The test suite lives under `scripts/test_*.py`. It uses stdlib `unittest` patterns and runs under pytest:

```bash
python3 -m pytest -q
```

Current baseline after GSD initialization:

```text
244 passed, 5 skipped, 2 subtests passed
```

## Important Focused Tests

- `scripts/test_converter.py` - Sigma conversion behavior.
- `scripts/test_sentinel_converter.py` - KQL/Sentinel conversion behavior.
- `scripts/test_sentinel_conversion_workflow.py` - Sentinel workflow status/promotion/reporting behavior.
- `scripts/test_deploy_dashboard.py` - dashboard/query/layout validation.
- `scripts/test_app_query_contract.py` - app/APM query source and field contract.
- `scripts/test_setup_log_sources.py` - parser/source field mapping contract.
- `scripts/test_generate_dashboard_data.py` and `scripts/test_generate_test_logs.py` - synthetic dataset generation.
- `scripts/test_catalog.py` - catalog generation and inventory assumptions.
- `scripts/test_query_audit.py` - live query audit helper behavior with mocked OCI clients.

## Quality Gates

Run these depending on change type:

```bash
python3 -m pytest -q
python3 scripts/audit_rule_quality.py --report docs/RULE_QUALITY_REPORT.md
python3 scripts/deploy_dashboard.py --dry-run
python3 scripts/release_checklist.py
```

For Sentinel-specific work:

```bash
python3 -m pytest scripts/test_sentinel_converter.py scripts/test_sentinel_conversion_workflow.py -q
python3 scripts/sentinel_conversion_workflow.py status --json --strict
```

For app/APM/dashboard work:

```bash
python3 -m pytest scripts/test_app_query_contract.py scripts/test_deploy_dashboard.py scripts/test_setup_log_sources.py -q
python3 scripts/deploy_dashboard.py --export-inventory
python3 scripts/deploy_dashboard.py --dry-run
```

## Live Validation

Live OCI validation requires explicit operator intent and profile setup. Do not assume live access in local-only GSD phases.

Examples:

```bash
python3 scripts/verify_deployed_dashboards.py --lookback 21d --query-timeout 60 --json docs/health/all-dashboard-verify.json
python3 scripts/sentinel_conversion_workflow.py promote --top all --timeout 20
```

## Skips

Some schema tests skip when generated NDJSON datasets are not present. This is expected in clean local runs unless the relevant synthetic data has been generated.
