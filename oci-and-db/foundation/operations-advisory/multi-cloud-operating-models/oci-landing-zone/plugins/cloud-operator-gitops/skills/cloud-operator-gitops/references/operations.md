# Operations

1. Validate `deployment-contract.json` and active GitHub authentication.
2. Resolve one canonical project slug and its allowed environment without inference.
3. Read the configured environment blueprint from exact landing-zone `main`.
4. Create a disposable clone and branch from exact `origin/main`.
5. Add one project to the protected catalog, generate its canonical OP04 file
   from the pinned OE release, and run `validate-onboarding.py`.
6. Show paths, semantic changes, base SHA, content hash, and `GitHub writes: none`.
7. Require fresh confirmation, revalidate the hashes, push, and open one PR.
8. Stop before merge. After human merge, monitor only the exact OP04 workflow.
9. Download only that successful run's JSON and Markdown artifacts and validate
   them together with `validate-handoff.py`. Derive the target repository,
   layout, and handoff path only from its output.
   Require the three workload-role compartment values to identify the same
   official OE `v3.1.0` project compartment.
10. Resolve the exact template repository and immutable revision for that
    layout from `deployment-contract.json`. If the target is absent, preview
    and separately confirm creation of one private repository, then verify its
    initial tree matches the pinned template. If an exact shared
    non-production target already exists, reuse it; never recreate or
    overwrite it.
11. For a new repository, create a unique
    `agent/project-handoff-<project>-<base-sha-prefix>` branch and run
    `render-project-repository.py`. It must initialize the exact target,
    contract-selected security profile, active CODEOWNERS, and selected
    environment handoff together. Run `validate-project-repository.py`; fail
    if any other path changes or any placeholder remains. For an existing
    initialized shared repository, verify those protected files and write only
    the new validated environment handoff.
12. If the operator explicitly requests registration of a verified externally
    deployed regular ExaCS database, also update the platform-owned
    `environments/<environment>/exacs-databases.json` registry. Show every
    path, source and content hashes, branch, and semantic summary with
    `GitHub writes: none`; require fresh confirmation and revalidate.
13. Push the validated branch and conditionally open one PR. Stop before merge
    and report the repository, environment, handoff path, and PR state.

Discard confirmation after interruption or Git drift. Never reuse an OP04
confirmation for repository creation or handoff publication; each write stage
requires its own preview and fresh confirmation.

Run commands directly and never generate helper executables. Register cleanup as soon as a
temporary workspace is created and remove it when the operation ends or is abandoned. Inventory
uses direct structured reads and leaves no local files.

Post-merge monitoring is continuous by default. Poll structured `gh run list` and `gh run view`
reads every 15–30 seconds until terminal. Treat missing, queued, pending, waiting, requested, and
in-progress states as progress, not a final answer. Keep the task active, report progress through
commentary only when status changes or about once per minute, and never require the user to return
and announce completion. Stop early only for an explicit one-time snapshot, user cancellation, or
repeated authentication/API failure.

For inventory, treat `{}` and a valid empty resource collection as zero declarations. Validate a
collection before extraction and do not use an empty iterator's exit status to label it
incomplete. Git declarations cannot prove whether a resource is currently running or stopped.
