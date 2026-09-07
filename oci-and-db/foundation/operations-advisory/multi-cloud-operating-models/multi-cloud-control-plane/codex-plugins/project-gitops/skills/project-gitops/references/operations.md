# Operations

1. Parse `mccp-installation.json` with `jq -e`, reject unresolved placeholders,
   derive its canonical catalog repository/ref, then validate `gh`
   authentication, exact private repository metadata, canonical project
   repository name, exact `main` SHA, and the selected environment handoff. Do
   not require or report active `.github/CODEOWNERS`; a
   `.github/CODEOWNERS.template` is an accepted Project Team-owned starting
   point.
2. Resolve the validator-returned catalog repository through GitHub API at the
   validator-returned SHA and verify its blob hash internally. Include only the
   user-relevant catalog choice in the semantic preview; do not expose commit or
   blob hashes unless the user requests diagnostics.
3. For a new OCI Compute request, offer the Frankfurt `VM.Standard.A1.Flex`
   image already pinned in the approved OCI Compute catalog template and ask
   whether to use it or provide another regional image OCID. The user confirms
   the image choice manually before approval. Validate the selected OCID
   through the manifest contract, state whether it is the catalog default or a
   user-selected override in the preview, and write it only to
   `platform_image.ocid`. Never use OCI CLI or call a cloud API to resolve an
   image.
4. Create a fresh disposable parent directory, then clone into its child named
   exactly `nonprod-<project>` or `prod-<project>` and create one
   collision-free branch from exact `origin/main`. The shared-layout validator
   rejects an arbitrary clone-directory name.
5. Edit one canonical aggregate manifest. For `nonprod-<project>`, first run
   `validate-shared-layout.py` for the explicitly selected `dev`, `test`, or
   `uat` environment; then run `validate-change.py` for both non-production and
   production repositories. Use only
   `{cloud}/{environment}/{region}/...` manifest paths and the matching
   `environments/<environment>/environment_information.md` handoff.
   For OCI, use the schema-3 TBAC target from that handoff: Application for
   Compute, Database for ADB and ADB lifecycle, and Infrastructure for project
   NSGs. A lifecycle manifest is either `{}` to clear a completed request, or
   includes `database_compartment_id` and one or more start/stop targets. For OCI
   Compute, one validated change contains exactly one VM; use a separate change
   and pull request for each additional VM.
6. Require a user-provided CRQ matching `CRQ[0-9]{1,20}`. Show one semantic
   diff, destructive/replacement warnings, branch, and CRQ; keep validator
   hashes and metadata internal unless the user requests diagnostics, then stop
   for one fresh confirmation.
7. Revalidate the internally bound hashes, stage only the validated path,
   commit, push, and conditionally create one PR. If the candidate drifted,
   discard confirmation and return to step 6; never request a second
   hash-confirmation. Stop before merge.
8. After human merge, monitor only the configured exact workflow and merge commit. Report configuration and structured workflow results without inferring cloud state.

On interruption, discard stale confirmation and rebuild the preview from exact remote state.

Post-merge monitoring is continuous by default. Poll structured `gh run list` and `gh run view`
reads every 15–30 seconds until terminal. Treat missing, queued, pending, waiting, requested, and
in-progress states as progress, not a final answer. Keep the task active, report progress through
commentary only when status changes or about once per minute, and never require the user to return
and announce completion. Stop early only for an explicit one-time snapshot, user cancellation, or
repeated authentication/API failure.

Run commands directly and never generate helper executables. Status and monitoring use structured
reads without cloning or local files. Register cleanup when a writable temporary workspace is
created and remove it when the operation ends or is abandoned.
