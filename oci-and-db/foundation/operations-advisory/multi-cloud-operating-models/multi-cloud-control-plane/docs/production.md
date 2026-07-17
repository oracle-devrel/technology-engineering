# Production repository model

Production uses a dedicated `prod-<project>` repository created from
`components/prod-project-template`. Its `production-v1` contract permits
only the `prod` GitHub Environment and manifest paths of the form
`<cloud>/prod/<region>/...`. Terraform state, runner labels, CODEOWNERS and
handoffs are therefore separate from `nonprod-<project>`.

Create a dedicated production approver team before creating the repository,
replace `__PROJECT__` in the template, and configure `READINESS_MARKER` plus
workload secrets only in the `prod` Environment. Require independent approval,
code-owner review, passing plans, and isolated production runners. Run the
[environment-secret end-to-end verification](environment-secret-e2e.md) against
production with a disposable manifest before accepting a real production request.
