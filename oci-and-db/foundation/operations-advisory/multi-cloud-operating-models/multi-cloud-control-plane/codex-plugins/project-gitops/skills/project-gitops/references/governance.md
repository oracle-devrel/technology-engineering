# Governance

Require a user-provided CRQ matching `CRQ[0-9]{1,20}` before preparing a
mutable manifest, lifecycle, branch-push, or pull-request change. Do not ask
for a CRQ for status, validation, or monitoring.

Before every branch push or pull-request creation, show one concise semantic
preview. Include the requested change, destructive or replacement impact,
branch, and CRQ. State `GitHub writes: none`, then ask: `Do you confirm? Reply
"confirm".` Accept that standalone reply case-insensitively. It applies only
to the previewed candidate on the then-current `main`. If the candidate or
`main` drifts, discard confirmation, regenerate the preview, and request a new
confirmation. Do not show, request, or require hashes or SHAs.

Human review and merge are mandatory. After a known human merge, read its
`mergeCommit.oid` with `gh pr view <number> --repo <owner/repository> --json
mergedAt,mergeCommit,url`, then identify the configured `push` workflow (not
the earlier PR run) with `gh run list --repo <owner/repository> --commit
<merge-commit-oid> --limit 10 --json
databaseId,status,conclusion,workflowName,url,event,headSha`. Select the
matching `push` run and monitor it until terminal unless the user asks for a
one-time snapshot. Poll structured GitHub reads every 15 to 30 seconds. Treat
queued and running states as progress. Report only material state changes in
commentary. Stop on explicit cancellation or repeated authentication or API
failure.
