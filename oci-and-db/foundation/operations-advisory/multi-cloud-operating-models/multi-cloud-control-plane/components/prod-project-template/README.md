# Production project template

This template creates one `prod-<project>` repository under the explicit
`production-v1` contract. Production is separate from shared non-production;
it uses only the `prod` deployment environment, production-isolated runners and
production approvers. Manifest paths are `<cloud>/prod/<region>/...` and the
handoff is `environments/prod/environment_information.md`.

Replace `__PROJECT__` and the CODEOWNERS team before granting project access.
Keep the default `github-environments` profile on paid plans and follow the
production runbook. For the GitHub Free `repository-secrets` fallback,
configure `GITOPS_SECRET_VALUES_PROD` as the JSON Actions repository secret and
set the `CONTROL_PLANE_READY_PROD` repository variable to `true`. Bundle keys
and runtime placeholders must begin with `PROD_`. Require independent
production approval and passing checks; do not use `secrets: inherit`.

Production supports Day 1 Terraform only in this release. Lifecycle operations
(Day 2), including ADB start/stop and `deploy-agent`, are not available because
this template intentionally has no Ansible caller workflow.
