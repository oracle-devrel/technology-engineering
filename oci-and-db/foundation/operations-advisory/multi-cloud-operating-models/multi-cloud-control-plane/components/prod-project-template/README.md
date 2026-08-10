# Production project template

This template creates one `prod-<project>` repository under the explicit
`production` contract. Production is separate from shared non-production;
it uses only the `prod` deployment environment, production-isolated runners,
and independent production reviewers. Manifest paths are
`<cloud>/prod/<region>/...` and the handoff is
`environments/prod/environment_information.md`.

The seeded region folders are examples. Before onboarding production in
another region, rename each enabled cloud region folder and complete the
production handoff with the approved regional references.

On GitHub Free, add a handed-off repository only to the organization runner
group reserved for production projects. Do not share that group with
non-production repositories. GitHub Free review is procedural; use the
paid-plan hardening model when enforceable approval controls are required.

Render the project target and `.github/CODEOWNERS.template` to an active
`.github/CODEOWNERS` file with valid existing owners before granting project
access.
New repositories can use the protected Platform CI workflows immediately after
the rendered workflow policy, CODEOWNERS, handoff, and runner routing are in
place. Configure `GITOPS_SECRET_VALUES_PROD` only when a workload manifest
contains a `__PROD_...__` placeholder. Bundle keys and runtime placeholders
must begin with `PROD_`. Require independent production approval and passing
checks; do not use `secrets: inherit`.

See the
[production runbook](../../docs/production.md)
before enabling automation. The paid-plan enforcement model is described in
the [final environment hardening guide](../../docs/final-environment-hardening.md).

Production supports the same supplied OCI Day 2 lifecycle operations as
non-production: ADB start/stop and `deploy-agent`. The visible
`lifecycle_operations/` directory contains no operation request; the UI or a
focused pull request creates the JSON request when an approved operation is
needed.
