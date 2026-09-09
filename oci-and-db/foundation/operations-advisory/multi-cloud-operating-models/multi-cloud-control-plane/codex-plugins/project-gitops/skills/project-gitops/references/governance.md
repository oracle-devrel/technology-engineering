# Governance

Require a user-provided CRQ matching `CRQ[0-9]{1,20}` before preparing a
mutable manifest, lifecycle, branch-push, or pull-request change. Do not ask
for a CRQ for status, validation, or monitoring.

Before every branch push or pull-request creation, show one concise semantic
preview. Include the requested change, destructive or replacement impact,
branch, and CRQ. State `GitHub writes: none`, then ask: `Do you confirm? Reply
"Confirm".` Accept only that exact reply. Bind it to the validated base and content hashes. If the
candidate drifts, discard confirmation, regenerate the preview, and request a
new confirmation. Do not ask for a separate hash confirmation.

Human review and merge are mandatory. After a known human merge, monitor the
configured exact workflow and merge commit until terminal unless the user asks
for a one-time snapshot. Poll structured GitHub reads every 15 to 30 seconds.
Treat queued and running states as progress. Report only material state changes
in commentary. Stop on explicit cancellation or repeated authentication or API
failure.
