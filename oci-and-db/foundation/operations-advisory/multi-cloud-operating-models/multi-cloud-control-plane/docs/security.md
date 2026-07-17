# Security

Project Teams submit requests through Git but do not receive deployment
credentials. Protected workflows use trusted runner identities to access cloud
services and Terraform state after approval.

Before production rollout:

- Keep shared and project repositories private. Protect `main` on a paid plan;
  on GitHub Free, restrict administration and direct pushes by policy.
- Require a successful plan or check and human approval. Enforce independent
  approval with paid-plan repository controls.
- Pin shared workflows, GitHub Actions, catalogs, and orchestrators to approved
  versions.
- Separate Terraform state by organization, project, cloud, environment, and
  region.
- Give each runner identity only the permissions required for its cloud and
  workload scope.
- Resolve credentials and passwords at runtime; never store them in manifests,
  handoffs, the UI, or the Codex app.
- Keep one JSON Actions repository secret per environment. The default-branch
  caller passes exactly one bundle to pinned Platform CI and rejects forks,
  workflow changes, mixed tuples, and cross-environment placeholders.
- Test failed plans, partial deployments, state recovery, runner isolation, SSH
  host verification, and audit evidence in non-production.

The optional UI and Codex app assistant can create Git changes only. They cannot
call cloud APIs, hold deployment credentials, merge their own pull requests, or
control deployment workflows.

Review these controls against your organization's security, compliance, data
residency, and change-management requirements before enabling production use.
