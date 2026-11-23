# PR review and explicit merge — Codex only

The skill stops after the [PR decision summary](workflow.md#pr-decision-summary) by default. In Codex, the user may then explicitly request `Merge PR #123` or name its exact URL in the already identified project repository. That instruction authorizes only the reviewed PR and version. Resolve the repository from context; ask if ambiguous, and reject another organization, a foundation/platform repository, a fork or a PR outside the handed-off project scope. The web UI cannot merge, even if asked; keep its host restrictions and direct the user to GitHub.

A `confirm` for branch/PR publication or secret preparation never authorizes merge. Do not infer authorization from green checks, a recorded approval, a plan to merge later, or a request to merge any future successful PR. An explicit exact-PR instruction after the summary needs no repeated `confirm` for the same unchanged action. If there is no prior summary for this exact version, produce it and wait for a new explicit merge instruction.

## Review and readiness

These are read-only checks for both the decision summary and the final merge recheck. Read structured metadata and reviews, including all review pages:

```bash
gh pr view <number> --repo multicloud-control-plane/<repository> \
  --json number,url,title,body,author,state,isDraft,isCrossRepository,baseRefName,baseRefOid,headRefName,headRefOid,mergeable,mergeStateStatus,reviewDecision,statusCheckRollup,autoMergeRequest,mergedAt,mergeCommit
gh api --paginate repos/multicloud-control-plane/<repository>/pulls/<number>/reviews \
  --jq '.[] | {id,reviewer:.user.login,reviewerType:.user.type,state,commit_id,submitted_at,html_url}'
gh api graphql -f repository='<repository>' \
  -f query='query($repository:String!){repository(owner:"multicloud-control-plane",name:$repository,followRenames:false){nameWithOwner isPrivate mergeCommitAllowed viewerPermission mergeQueue(branch:"main"){id}}}'
```

Require all of the following before reporting `Ready to request merge` or attempting merge:

- The exact handed-off private project repository, CRQ and catalog-selected scope are established. The PR is open, not a draft or cross-repository request, targets `main`, and its files/configuration match the reviewed request. Missing intent or unexplained additional impact blocks readiness.
- The expected current-head workflow is successful and the trusted Platform CI safe plan/check evidence matches its exact commit, run and attempt. All required checks are satisfied, with no failed or pending checks relevant to this change. Do not treat missing checks, skipped validation, an old attempt or a comment from an untrusted author as success. Use the existing workflow/evidence matching; do not build a second validator.
- At least one current effective `APPROVED` review is by a human (`reviewerType: User`) other than the PR author, with `commit_id` equal to the current head. Process all reviews chronologically per reviewer: a later approval, changes request or dismissal changes that person's effective decision; comments and pending reviews do not clear a changes request. No reviewer may have an outstanding effective `CHANGES_REQUESTED`, including on an older revision. A bot, self-approval, chat assurance, PR comment, dismissed or stale approval does not satisfy independent review. Respect any additional reviewer/CODEOWNERS requirements enforced by GitHub; `reviewDecision` alone is not proof of current-head independent approval.
- GitHub reports `mergeable: MERGEABLE` and `mergeStateStatus: CLEAN`. Unknown, conflicting, behind, blocked or otherwise non-clean states remain blocked/unverified. The current identity has repository write, maintain or admin permission, merge commits are allowed, and the `main` merge queue is absent. A non-null queue, existing `autoMergeRequest`, denied/incomplete metadata or a repository restriction blocks this direct-merge path. Never substitute squash/rebase, enqueue, enable auto-merge, or bypass a restriction. An empty approval requirement on the GitHub Free profile does not remove this skill's independent-review requirement.

The [GitHub review API](https://docs.github.com/en/rest/pulls/reviews#list-reviews-for-a-pull-request) supplies review identity, state and commit. [Repository metadata](https://docs.github.com/en/graphql/reference/repos#repository) supplies merge-commit permission and the branch merge queue. Query failures or GraphQL errors leave readiness unverified; do not interpret missing/null repository data as permission or absence of a queue. A valid repository object with an explicitly null `mergeQueue` is the no-queue case.

## Execute only the reviewed version

After an explicit exact-PR instruction, repeat the readiness checks immediately before mutation and re-read head/base after collecting evidence. Compare them with the head/base recorded for the decision summary on which the user acted, and recheck the matching workflow's current run/attempt and review state. If head, base, scope or impact changed, do not merge: refresh the evaluation and summary and require a new explicit merge instruction. If checks, review or permissions became unsatisfied, report the blocker and stop; do not leave an authorization queued for later automatic use. A changed run/attempt requires fresh matching evidence and an updated decision summary before a new merge instruction.

Use the known current `headRefOid` as the internal expected SHA; do not ask the user to supply it. Only when every condition still passes, execute this single action with the exact repository and PR number:

```bash
gh pr merge <number> --repo multicloud-control-plane/<repository> \
  --merge --match-head-commit <reviewed-head-sha>
```

Do not use `--admin`, `--auto`, `--delete-branch`, a default/current-branch PR selection, automatic retries, branch updates or workflow controls. The [head-match guard](https://cli.github.com/manual/gh_pr_merge) rejects a concurrent head change; it does not atomically lock the base or review/check settings. The final reads reduce that gap, and GitHub still applies its repository controls. Do not claim stronger concurrency protection or GitHub-enforced review where the repository uses procedural controls.

If the command fails or its outcome is uncertain, read the exact PR state before any further action. Never retry the mutation blindly. If the PR remains open, report the blocker/uncertainty and stop. If it was merged, verify the recorded head matches the reviewed head and obtain the actual `mergeCommit.oid` and `mergedAt`; do not claim to have performed a merge completed by another actor. If it was already merged before the instruction, do not merge again; report that fact and monitor its matching execution. A closed unmerged PR remains closed; do not reopen it.

Only a verified merge starts [post-merge monitoring](governance.md). Match the configured `push` workflow to the actual merge commit and follow it to its recorded result, using the existing progress updates. Missing or ambiguous execution evidence stays unverified; never dispatch or rerun a workflow to obtain it. A successful merge is not a successful deployment or lifecycle operation.
