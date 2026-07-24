# Production repository model

Production uses a dedicated `prod-<project>` repository created from
`components/prod-project-template`. Its `production-v1` contract permits
only the `prod` deployment environment and manifest paths of the form
`<cloud>/prod/<region>/...`. Terraform state, runner labels, CODEOWNERS and
handoffs are therefore separate from `nonprod-<project>`.

Production supports Day 1 Terraform only in this release. Lifecycle operations
(Day 2), including ADB start/stop and `deploy-agent`, are unsupported because
the production template has no Ansible workflow.

Publish the prepared `prod-project-template` repository from the deployment
runbook and create `prod-<project>` from that exact pinned template. Replace
`__PROJECT__`, install the verified production handoff at
`environments/prod/environment_information.md`. Select one repository-wide
security profile in `control-plane.json`. Use the
[GitHub plan capability matrix](security.md#github-plan-capability-matrix)
before configuring the repository.

The recommended paid-plan profile is `github-environments`. Create the `prod`
base Environment for plans and `prod-apply` for apply. Do not configure
reviewers on the base Environment. On Enterprise private repositories,
configure required reviewers and prevention of self-review on `prod-apply`;
those two controls are unavailable for private repositories on Pro/Team. Set
identical secrets in both Environments. Also create the two non-sensitive
repository sentinels required by the reusable-workflow secret channel:

```bash
gh secret set GITOPS_SECRET_VALUES --env prod --repo OWNER/prod-PROJECT
gh secret set READINESS_MARKER --env prod --repo OWNER/prod-PROJECT
gh secret set GITOPS_SECRET_VALUES --env prod-apply --repo OWNER/prod-PROJECT
gh secret set READINESS_MARKER --env prod-apply --repo OWNER/prod-PROJECT
printf '{"INVALID":"true"}\n' | gh secret set GITOPS_SECRET_VALUES --repo OWNER/prod-PROJECT
printf 'false\n' | gh secret set READINESS_MARKER --repo OWNER/prod-PROJECT
```

The selected Environment overrides these repository sentinels. Keep the
Environment copies synchronized; never place real credential values in the
sentinels.

Run the [GitHub Environment end-to-end verification](environment-secret-e2e.md)
against a disposable production manifest.

For the GitHub Free fallback, set `security_profile` to `repository-secrets`
and configure:

```bash
gh secret set GITOPS_SECRET_VALUES_PROD --repo OWNER/prod-PROJECT
gh variable set CONTROL_PLANE_READY_PROD --body true --repo OWNER/prod-PROJECT
```

The secret commands prompt for values; never put literal members on a command
line or in Git. GitHub Free private repositories cannot enforce branch
protection, CODEOWNERS review, or Environment approval. Restrict repository
administration and direct pushes, record an independent PR review, and verify
the successful production plan on the current commit before merge.

Before creating the production repository, render
`.github/CODEOWNERS.template` as `.github/CODEOWNERS` with valid existing
owners. Keep `.github`, `control-plane.json`, and `environments` under platform
ownership; use a dedicated production approver team or user for the production
workload paths. Replace `__PROJECT__` in the template and configure exactly the
secret source selected by `security_profile`. Every bundle key and runtime
placeholder must begin with `PROD_`. On paid plans, enforce independent
approval and code-owner review using the branch-protection baseline in the
deployment runbook. On every plan, verify the result for the current commit
before merge. Use an isolated production runner in every profile. For the Free
fallback, run the
[repository-secret end-to-end verification](repository-secret-e2e.md) against
production with a disposable manifest before accepting a real request.
