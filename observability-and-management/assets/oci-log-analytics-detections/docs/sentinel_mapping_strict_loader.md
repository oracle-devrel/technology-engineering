# Sentinel Mapping Strict Loader

**First run:** 2026-05-17

Phase 7 moved the Sentinel-to-Logan mapping editing surface to `config/mapping/` and made `scripts/kql/mapping_loader.py` the authoritative loader. The loader rejects duplicate YAML keys before merge and also rejects cross-shard duplicate table or field keys.

## Findings

- The generated shard set strict-loads successfully.
- The generated compatibility export `config/sentinel_oci_mapping.yaml` strict-loads successfully.
- No duplicate-key overrides were found in the generated Phase 7 shard layout.
- Role metadata is present for every mapped field and is validated against `subject`, `target`, `initiator`, `resource`, `time`, `hash`, and `network`.

## Reproduce

```bash
python3 scripts/generate_mapping_config.py --export-compat
python3 scripts/lint_mapping_collisions.py --check
python3 -m pytest scripts/test_mapping_loader.py -q
```

To verify the duplicate-key failure path, add a duplicate field key to any shard under `config/mapping/fields/` and run:

```bash
python3 -m pytest scripts/test_mapping_loader.py -q
```

The loader raises a structured reason in the form `duplicate_key:<path>:<key>`.

## Operating Notes

- Edit `config/mapping/_root.yaml` and shard files under `config/mapping/`; do not hand-edit `config/sentinel_oci_mapping.yaml`.
- Regenerate the compatibility export with `python3 scripts/generate_mapping_config.py --export-compat`.
- Regenerate the collision inventory with `python3 scripts/lint_mapping_collisions.py`.
- Treat new collision reasons in `queries/mapping_collisions.json` as review-required before promoting related Sentinel detections.
