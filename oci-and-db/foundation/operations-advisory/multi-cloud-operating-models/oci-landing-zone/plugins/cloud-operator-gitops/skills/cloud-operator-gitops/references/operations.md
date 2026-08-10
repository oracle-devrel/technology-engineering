# Operations

1. Parse `cloud-operator-installation.json` with `jq -e`, reject unresolved
   placeholders, verify its schema 3 foundation selection and explicit
   `project_templates` repository/revision pairs, then validate active GitHub
   authentication.
2. Resolve one canonical project slug and its allowed environment without inference.
   The DNS name must omit the repository prefix derived by the skill: `nonprod-`
   for dev/test/UAT and `prod-` for prod.
3. Read the configured environment blueprint from the exact configured
   foundation repository at `main`; require its provenance repository to match.
4. Create a disposable clone from exact `origin/main`, then before running
   `render-op04.py` create and switch to
   `agent/project-onboard-<environment>-<dns-name>-<first-12-of-origin/main>`.
   Running the generator or `validate-onboarding.py` from `main` is invalid;
   never bypass, modify, or infer the validator's branch contract.
5. Require a user-provided CRQ matching `CRQ[0-9]{1,20}`, then add one
   project to the protected catalog, generate its canonical OP04 file
   from the pinned OE release, and run `validate-onboarding.py`.
6. Show affected paths, semantic changes, the CRQ, and `GitHub writes: none`; keep
   validator hashes and metadata internal unless the user asks for diagnostics.
7. Require fresh confirmation, revalidate internally, push, and open one PR.
8. Stop before merge. After human merge, monitor only the exact OP04 workflow.
9. Download only that successful run's JSON and Markdown artifacts and validate
   them together with `validate-handoff.py`. Derive the target repository,
   layout, and handoff path only from its output.
   Require schema 3: a TBAC project root and distinct App, DB, and
   Infrastructure compartment OCIDs.
10. Resolve the exact template repository and immutable revision for that
    layout from `cloud-operator-installation.json`. If the target is absent,
    preview and separately confirm creation of one private empty repository,
    push the exact source revision as `main`, then verify the target commit and
    tree match that source. Never use a default branch, template redirect, or
    SHA-only repository discovery. If an exact shared
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
12. Push the validated branch and conditionally open one PR. Stop before merge
    and report the repository, environment, handoff path, and PR state.
13. When reporting a merged handoff for a GitHub Free private repository,
    state that a repository secret bundle is required only for a workload with
    matching environment-qualified placeholders. Organization-scoped private
    `platform-ci` Actions access is configured once on Platform CI and
    inherited automatically by new organization repositories. Do not receive,
    print, or set secret values. State that the repository-secret end-to-end
    verification must pass before a secret-backed workload request. Never
    instruct a deploy key, personal access token, or branch reference for
    Platform CI source access.

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

## Project retirement

1. Resolve one handed-off environment and collect the required workload, lifecycle, teardown,
   CRQ, retention, repository-preservation, and human-approval evidence. The
   CRQ must match `CRQ[0-9]{1,20}`.
2. Create a disposable landing-zone clone from exact `origin/main` and remove one project name
   from its environment in `config/projects.json` plus that project's generated `iam.json`.
3. Run `validate-retirement.py --evidence <file> --repository <clone> --base-ref <sha> --project
   <environment>-<project>`. Stop if any other path or catalog value changed.
4. Show the concise semantic preview, require fresh confirmation, revalidate internally, then push one
   branch and conditionally open one pull request. Stop before merge.
5. After human merge, monitor the existing OP04 workflow to terminal. Disable the retired
   environment and restore its handoff placeholder only through a separate reviewed change.
