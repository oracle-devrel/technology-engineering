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

Configure one JSON Actions repository secret per enabled environment:
`GITOPS_SECRET_VALUES_DEV`, `GITOPS_SECRET_VALUES_TEST`, or
`GITOPS_SECRET_VALUES_UAT`. Configure the matching
`CONTROL_PLANE_READY_<ENVIRONMENT>` repository variable with value `true`.
Bundle keys and runtime placeholders must begin with the selected uppercase
environment. Do not use `secrets: inherit` or combine environments.
