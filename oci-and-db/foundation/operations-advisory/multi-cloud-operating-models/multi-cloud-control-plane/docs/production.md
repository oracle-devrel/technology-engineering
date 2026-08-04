# Production repository model

Production uses a dedicated `prod-<project>` repository created from
`components/prod-project-template`. Its `production-v1` contract permits only
the `prod` deployment environment and paths of the form
`<cloud>/prod/<region>/...`. Terraform state, runner labels, CODEOWNERS, and
handoffs are separate from `nonprod-<project>`.

Production supports Day 1 Terraform only in this release. Lifecycle operations
(Day 2), including ADB start/stop and `deploy-agent`, are unsupported because
the production template has no Ansible workflow.

Publish the prepared `prod-project-template` repository from the deployment
runbook and create `prod-<project>` from that exact pinned template. Replace
`__PROJECT__`, install the verified production handoff at
`environments/prod/environment_information.md`, and configure the fixed MVP
`repository-secrets` profile:

```bash
gh secret set GITOPS_SECRET_VALUES_PROD --repo OWNER/prod-PROJECT
gh variable set CONTROL_PLANE_READY_PROD --body true --repo OWNER/prod-PROJECT
```

The secret command prompts for values; never put literal members on a command
line or in Git. GitHub Free private repositories cannot enforce private branch
protection, CODEOWNERS review, or Environment approval. Restrict repository
administration and direct pushes, record an independent PR review, and verify
the successful production plan on the current commit before merge.

Before creating the production repository, render
`.github/CODEOWNERS.template` as `.github/CODEOWNERS` with valid existing
owners. Keep `.github` and `environments` under platform ownership; use a
dedicated production approver team or user for production workload paths.
Every bundle key and runtime placeholder must begin with `PROD_`. Use an
isolated production organization runner group restricted to selected production
repositories and run the
[repository-secret end-to-end verification](repository-secret-e2e.md) with a
disposable manifest before accepting a real request.

The paid-platform hardening design is documented separately in
[final-environment-hardening.md](final-environment-hardening.md). It is not a
profile switch in this MVP.
