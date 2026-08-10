# Shared non-production project template

This template creates `nonprod-<project>` repositories using the explicit
`shared-nonprod-v2` contract. This package is for initial installations and
does not support another repository layout.

Manifest paths are `<cloud>/<environment>/<region>/...`; handoffs are stored at
`environments/<environment>/environment_information.md`. Allowed environments
are lowercase `dev`, `test`, and `uat`. Production aliases are permanently
rejected. The default branch owns workflows and CODEOWNERS. On GitHub Free its
governance is procedural; a plan that supports them can enforce branch
protection and required reviews. The rendered workflows contain the fixed
`repository-secrets` security profile and derive runner labels from the cloud
and environment. Project changes may contain one cloud/environment/region
tuple.

The seeded region folders are examples. Before onboarding a project in another
region, rename each enabled cloud/environment region folder and complete the
matching environment handoff with the approved regional references.

On GitHub Free, add a handed-off repository only to the organization runner
group reserved for non-production projects. Do not share that group with
production repositories.

Before creating a project repository, render `.github/CODEOWNERS.template` to
an active `.github/CODEOWNERS` file with valid existing platform and
environment owners. Do not publish the generic template placeholders as active
CODEOWNERS rules.

New repositories can use the protected Platform CI workflows immediately after
the rendered workflow policy, CODEOWNERS, handoff, runner routing, and
documented procedural review—or supported-plan branch protection—are in place.

Configure a JSON Actions repository secret only when a workload manifest for an
enabled environment contains a secret placeholder. Use the matching environment
secret:
`GITOPS_SECRET_VALUES_DEV`,
`GITOPS_SECRET_VALUES_TEST`, or `GITOPS_SECRET_VALUES_UAT`. Bundle keys and
runtime placeholders must begin with the selected
uppercase environment. Do not use `secrets: inherit` or combine environments.

See the
[shared non-production runbook](../../docs/shared-nonproduction.md)
before enabling automation. The paid-plan enforcement model is described in
the [final environment hardening guide](../../docs/final-environment-hardening.md).
