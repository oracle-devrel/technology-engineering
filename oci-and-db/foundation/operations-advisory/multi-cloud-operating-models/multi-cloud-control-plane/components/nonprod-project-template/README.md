# Shared non-production project template

This template creates `nonprod-<project>` repositories using the explicit
`shared-nonprod-v2` contract. This package is for initial installations and
does not support another repository layout.

Manifest paths are `<cloud>/<environment>/<region>/...`; handoffs are stored at
`environments/<environment>/environment_information.md`. Allowed environments
are lowercase `dev`, `test`, and `uat`. Production aliases are permanently
rejected. The protected default branch owns workflows and CODEOWNERS. The
rendered workflows contain the fixed `repository-secrets` security profile and
derive runner labels from the cloud and environment. Project changes may
contain one cloud/environment/region tuple.

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

New repositories are inactive by default. Set the repository variable
`PROJECT_AUTOMATION_READY` to `true` only after the rendered workflow policy,
CODEOWNERS, handoff, secrets, readiness markers, runner routing, and branch
protection are all in place.

Configure one JSON Actions repository secret per enabled environment:
`GITOPS_SECRET_VALUES_DEV`,
`GITOPS_SECRET_VALUES_TEST`, or `GITOPS_SECRET_VALUES_UAT`. Configure the
matching `CONTROL_PLANE_READY_<ENVIRONMENT>` repository variable with value
`true`. Bundle keys and runtime placeholders must begin with the selected
uppercase environment. Do not use `secrets: inherit` or combine environments.

See the
[shared non-production runbook](https://github.com/oracle-devrel/technology-engineering/blob/OperationsAdvisory-updates2/oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/docs/shared-nonproduction.md)
before enabling automation. The paid-plan enforcement model is described in
the [final environment hardening guide](https://github.com/oracle-devrel/technology-engineering/blob/OperationsAdvisory-updates2/oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/docs/final-environment-hardening.md).
