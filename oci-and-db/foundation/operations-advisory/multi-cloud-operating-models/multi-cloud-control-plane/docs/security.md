# Security

Project Teams submit requests through Git but do not receive deployment
credentials. Protected workflows use trusted runner identities to access cloud
services and Terraform state after approval.

Before production rollout:

- Keep shared and project repositories private. Use the recommended
  `github-environments` profile on paid plans, protect `main`, require
  CODEOWNERS and successful checks, and configure Environment reviewers where
  the private-repository plan supports them. Use `repository-secrets` only as
  the GitHub Free fallback, with administration and direct pushes restricted
  by policy.
- Require a successful plan or check and human approval. GitHub Environment
  secrets and protected branches strengthen every paid tier and provide
  deployment history. Required Environment reviewers and prevention of
  self-review enforce an additional boundary on Enterprise private
  repositories; Free-profile approval remains procedural.
- Pin shared workflows, GitHub Actions, catalogs, and orchestrators to approved
  versions.
- Separate Terraform state by organization, project, cloud, environment, and
  region.
- Give each runner identity only the permissions required for its cloud and
  workload scope.
- Resolve credentials and passwords at runtime; never store them in manifests,
  handoffs, the UI, or the Codex app.
- In `github-environments`, keep `GITOPS_SECRET_VALUES` and `READINESS_MARKER`
  in each selected GitHub Environment. In `repository-secrets`, keep one
  environment-qualified JSON repository secret and readiness variable per
  environment. The default-branch caller rejects forks, workflow changes,
  mixed tuples, and cross-environment placeholders in both profiles.
- Test failed plans, partial deployments, state recovery, runner isolation, SSH
  host verification, and audit evidence in non-production.

The optional UI and Codex app assistant can create Git changes only. They cannot
call cloud APIs, hold deployment credentials, merge their own pull requests, or
control deployment workflows.

Review these controls against your organization's security, compliance, data
residency, and change-management requirements before enabling production use.
