# Operations

1. Validate `deployment-contract.json` and active GitHub authentication.
2. Resolve one canonical project slug and its allowed environment without inference.
3. Read the configured environment blueprint from exact landing-zone `main`.
4. Create a disposable clone and branch from exact `origin/main`.
5. Render the canonical OP04 files and run `validate-onboarding.py`.
6. Show paths, semantic changes, base SHA, content hash, and `GitHub writes: none`.
7. Require fresh confirmation, revalidate the hashes, push, and open one PR.
8. Stop before merge. After human merge, monitor only the exact OP04 workflow.
9. Report the validated JSON and Markdown handoff artifacts, then stop.

Discard confirmation after interruption or Git drift. Project repository creation
and project-repository writes are outside this plugin.

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
