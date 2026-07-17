# Operations

1. Validate the deployment contract, `gh` authentication, exact private repository metadata, and exact `main` SHA.
2. Resolve the approved catalog file through GitHub API at the configured SHA and verify its blob hash.
3. Create a disposable clone and one collision-free branch from exact `origin/main`.
4. Edit one canonical aggregate manifest. For `nonprod-<project>`, first run
   `validate-shared-layout.py` for the selected environment; then run
   `validate-change.py` for both non-production and production repositories.
5. Show the semantic diff, destructive/replacement warnings, branch, base SHA, and content SHA-256; then stop for fresh confirmation.
6. Revalidate hashes, stage only the validated path, commit, push, and conditionally create one PR. Stop before merge.
7. After human merge, monitor only the configured exact workflow and merge commit. Report configuration and structured workflow results without inferring cloud state.

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
