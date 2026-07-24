# Production project template

This template creates one `prod-<project>` repository under the explicit
`production-v1` contract. Production is separate from shared non-production;
it uses only the `prod` deployment environment, production-isolated runners and
production approvers. Manifest paths are `<cloud>/prod/<region>/...` and the
handoff is `environments/prod/environment_information.md`.

Render the project target and `.github/CODEOWNERS.template` to an active
`.github/CODEOWNERS` file with valid existing owners before granting project
access.
New repositories are inactive by default. Set the repository variable
`PROJECT_AUTOMATION_READY` to `true` only after the rendered contract,
CODEOWNERS, handoff, secrets, readiness markers, runner routing, and branch
protection are all in place.
Keep the default `github-environments` profile on paid plans and follow the
production runbook. Required Environment reviewers and prevention of
self-review on private repositories require Enterprise. For the GitHub Free
`repository-secrets` fallback,
configure `GITOPS_SECRET_VALUES_PROD` as the JSON Actions repository secret and
set the `CONTROL_PLANE_READY_PROD` repository variable to `true`. Bundle keys
and runtime placeholders must begin with `PROD_`. Require independent
production approval and passing checks; do not use `secrets: inherit`.

See the
[GitHub plan capability matrix](../../docs/security.md#github-plan-capability-matrix)
and the [production runbook](../../docs/production.md) before enabling
automation.

Production supports Day 1 Terraform only in this release. Lifecycle operations
(Day 2), including ADB start/stop and `deploy-agent`, are not available because
this template intentionally has no Ansible caller workflow.
