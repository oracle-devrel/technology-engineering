# Eval-First Harness

A small, fixture-driven regression fence for the `dbman-opsi` enablement logic.
Every defect found by live testing against the cap tenancy is encoded here so it
can never silently return. Evals are organized by **defect/risk**, not by module,
so they survive refactors.

## The eval-first loop

1. **Define** a capability eval (intended behaviour) and a regression eval (a
   defect signature that must never recur).
2. **Baseline** — run before a change; a regression eval should *fail* on the
   broken code and *pass* once fixed (e.g. `R2_validate_cli_path_uses_live_reads`
   failed on `CommandRunner(dry_run=args.dry_run)` and passes on `dry_run=False`).
3. **Implement** the change.
4. **Compare deltas** — re-run; no capability eval regressed, the targeted
   regression eval flipped to green.

## Run

```bash
pytest -m eval --no-cov            # just the evals (skip the coverage gate)
pytest                             # evals run as part of the full suite
```

## Coverage map (defect → eval)

| ID | Defect signature (where it was found) | Eval |
|----|----------------------------------------|------|
| C1 | OPSI state must come from reliable GET-by-OCID | `test_capability::...active_via_reliable_get...` |
| C2 | NOT_FOUND only from a complete+stable absence | `test_capability::...complete_stable_absence` |
| R1 | Flaky OPSI LIST → false `NOT_FOUND` while ACTIVE | `test_regression::test_R1_*` |
| R2 | dry-run runner stubs every read to `{}` | `test_regression::test_R2_dry_run_runner_stubs_every_read` |
| R2 | `validate --dry-run` stubbed live reads | `test_regression::test_R2_validate_cli_path_uses_live_reads...` |
| R3 | list-first idempotency crashed on a real 409 | `test_regression::test_R3_*` |

Enable idempotency (skip-reconcile on already-enabled DBM, skip-create on ACTIVE
OPSI) is covered by `tests/test_enablement.py`; the merge/verdict internals by
`tests/test_validation.py` and `tests/test_oci_cli.py`. This harness adds the
cross-cutting defect-signature layer on top.

## Fixtures

`fakes.ReplayOci` models the two production behaviours that matter: the **flaky
aggregated LIST** (replays a `(items, complete)` sequence, one per call) and the
**reliable single-resource GET**. See its docstring.
