# Production project template

This template creates one `prod-<project>` repository under the explicit
`production-v1` contract. Production is separate from shared non-production;
it uses only the `prod` deployment environment, production-isolated runners and
production approvers. Manifest paths are `<cloud>/prod/<region>/...` and the
handoff is `environments/prod/environment_information.md`.

On GitHub Free, add a handed-off repository only to the organization runner
group reserved for production projects. Do not share that group with
non-production repositories.

Render the project target and `.github/CODEOWNERS.template` to an active
`.github/CODEOWNERS` file with valid existing owners before granting project
access.
New repositories are inactive by default. Set the repository variable
`PROJECT_AUTOMATION_READY` to `true` only after the rendered workflow policy,
CODEOWNERS, handoff, secrets, readiness markers, and runner routing are all in
place. Configure `GITOPS_SECRET_VALUES_PROD` as the JSON Actions repository secret and
set the `CONTROL_PLANE_READY_PROD` repository variable to `true`. Bundle keys
and runtime placeholders must begin with `PROD_`. Require independent
production approval and passing checks; do not use `secrets: inherit`.

See the
[production runbook](https://github.com/oracle-devrel/technology-engineering/blob/main/oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/docs/production.md)
before enabling automation. The paid-plan enforcement model is described in
the [final environment hardening guide](https://github.com/oracle-devrel/technology-engineering/blob/main/oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/docs/final-environment-hardening.md).

Production supports Day 1 Terraform only in this release. Lifecycle operations
(Day 2), including ADB start/stop and `deploy-agent`, are not available because
this template intentionally has no Ansible caller workflow.
