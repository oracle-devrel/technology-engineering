# Shared non-production project template

This template creates `nonprod-<project>` repositories using the explicit
`shared-nonprod-v2` contract. This package is for initial installations and
does not support another repository layout.

Manifest paths are `<cloud>/<environment>/<region>/...`; handoffs are stored at
`environments/<environment>/environment_information.md`. Allowed environments
are lowercase `dev`, `test`, and `uat`. Production aliases are permanently
rejected. The protected default branch owns `control-plane.json`, workflows,
and CODEOWNERS. Project changes may contain one cloud/environment/region tuple.

Before creating a project repository, render `.github/CODEOWNERS.template` to
an active `.github/CODEOWNERS` file with valid existing platform and
environment owners. Do not publish the generic template placeholders as active
CODEOWNERS rules.

New repositories are inactive by default. Set the repository variable
`PROJECT_AUTOMATION_READY` to `true` only after the rendered contract,
CODEOWNERS, handoff, secrets, readiness markers, runner routing, and branch
protection are all in place.

The platform team may register externally deployed regular ExaCS databases in
`environments/<environment>/exacs-databases.json`. This registry is a
platform-owned handoff artifact; project teams do not edit it. It binds a
subsequent reviewed out-of-place patch request to the approved database and
target Database Homes without requiring Terraform to have created the database.

Keep the default `github-environments` profile on paid plans. Create a
reviewer-free base Environment and a matching reviewer-protected
`<environment>-apply` Environment for each logical environment; required
Environment reviewers on private repositories require Enterprise.

For the GitHub Free `repository-secrets` fallback, configure one JSON Actions
repository secret per enabled environment: `GITOPS_SECRET_VALUES_DEV`,
`GITOPS_SECRET_VALUES_TEST`, or `GITOPS_SECRET_VALUES_UAT`. Configure the
matching `CONTROL_PLANE_READY_<ENVIRONMENT>` repository variable with value
`true`. Bundle keys and runtime placeholders must begin with the selected
uppercase environment. Do not use `secrets: inherit` or combine environments.

See the
[GitHub plan capability matrix](../../docs/security.md#github-plan-capability-matrix)
and the [shared non-production runbook](../../docs/shared-nonproduction.md)
before enabling automation.
